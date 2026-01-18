import React, { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'
import './StoryRibbons.css'

// Color schemes for event types
const eventTypeColors = {
  'INTERDICTION': '#7209b7',
  'VILLAINY': '#370617',
  'LACK': '#c1121f',
  'BEGINNING_COUNTERACTION': '#40916c',
  'DEPARTURE': '#219ebc',
  'FIRST_FUNCTION_DONOR': '#d4a373',
  'HERO_REACTION': '#e63946',
  'RECEIPT_OF_AGENT': '#2d6a4f',
  'STRUGGLE': '#dc2f02',
  'VICTORY': '#38b000',
  'RECOGNITION': '#9d4edd',
  'TRANSFIGURATION': '#f77f00',
  'WEDDING': '#ff006e',
  'PUNISHMENT': '#370617',
  'RESCUE': '#06d6a0',
  'UNRECOGNIZED_ARRIVAL': '#118ab2',
  'Initial Situation': '#6b6b6b',
  'OTHER': '#6b6b6b',
}

// Hero color - distinctive vermillion
const heroColor = '#d62828'

// Heatmap color scale: Cold (hostile) → Neutral → Warm (friendly)
// Using a diverging color scheme: Blue → Gray → Red
const heatmapColors = {
  '-2': '#1a5276',  // Deep blue (most hostile)
  '-1': '#5dade2',  // Light blue (negative)
  '0': '#aeb6bf',   // Gray (neutral)
  '1': '#f5b041',   // Orange (positive)
  '2': '#c0392b',   // Deep red (most friendly/romantic)
}

// Create D3 color interpolator for smooth heatmap
const createHeatmapScale = () => {
  return d3.scaleLinear()
    .domain([-2, -1, 0, 1, 2])
    .range([
      '#1a5276',  // Deep blue (most hostile)
      '#5dade2',  // Light blue (negative)  
      '#aeb6bf',  // Gray (neutral)
      '#f5b041',  // Orange (positive)
      '#c0392b',  // Deep red (most friendly)
    ])
    .clamp(true)
}

// Get color for a specific friendly level using heatmap
const getFriendlyLevelColor = (level) => {
  const scale = createHeatmapScale()
  return scale(level)
}

// Interpolate color based on friendly level (continuous heatmap scale)
const interpolateFriendlyColor = (level) => {
  // Clamp level to [-4, 4] for cumulative levels, then normalize to [-2, 2]
  const normalizedLevel = Math.max(-2, Math.min(2, level / 2))
  const scale = createHeatmapScale()
  return scale(normalizedLevel)
}

// Warm color palette for friendly characters (camp colors) - based on heatmap warm side
const warmColorPalette = [
  '#c0392b',  // Deep red (most friendly)
  '#e74c3c',  // Bright red
  '#f5b041',  // Orange
  '#f7dc6f',  // Light yellow-orange
  '#eb984e',  // Dark orange
  '#dc7633',  // Burnt orange
  '#ca6f1e',  // Caramel
  '#d35400',  // Pumpkin
  '#e67e22',  // Carrot orange
  '#f39c12',  // Sun yellow
]

// Cool color palette for hostile characters (camp colors) - based on heatmap cool side
const coolColorPalette = [
  '#1a5276',  // Deep blue (most hostile)
  '#2874a6',  // Dark blue
  '#5dade2',  // Light blue
  '#3498db',  // Dodger blue
  '#2980b9',  // Strong blue
  '#1f618d',  // Dark cyan blue
  '#154360',  // Very dark blue
  '#21618c',  // Lapis blue
  '#2e86ab',  // Steel blue
  '#1b4f72',  // Navy blue
]

// Neutral color palette
const neutralColorPalette = [
  '#aeb6bf',  // Gray (matches heatmap neutral)
  '#99a3a4',  // Dark gray
  '#bdc3c7',  // Silver
  '#d5d8dc',  // Light gray
  '#808b96',  // Slate gray
]

// Get CAMP color for character (used for center line)
// Uses total_level (sum of all friendly levels) to determine color intensity
const getCampColor = (char, index) => {
  const relationship = char.hero_relationship || 'neutral'
  
  if (relationship === 'hero') {
    return heroColor
  }
  
  // Use total_level to determine color from heatmap
  const totalLevel = char.total_level || 0
  
  // Use heatmap scale based on total_level
  // Normalize: clamp to reasonable range and map to color
  const scale = createHeatmapScale()
  
  if (relationship === 'friendly') {
    // Friendly camp - use total_level (positive values)
    // Map to warm side of heatmap
    const normalizedLevel = Math.min(2, Math.max(0, totalLevel))
    return scale(normalizedLevel)
  }
  
  if (relationship === 'hostile') {
    // Hostile camp - use total_level (negative values)
    // Map to cool side of heatmap
    const normalizedLevel = Math.max(-2, Math.min(0, totalLevel))
    return scale(normalizedLevel)
  }
  
  // Neutral - gray
  return scale(0)
}

// Alias for backward compatibility
const getCharacterColor = getCampColor

// Get relationship color for legend
const getRelationshipColor = (relationship) => {
  switch (relationship) {
    case 'hero': return heroColor
    case 'friendly': return warmColorPalette[0]
    case 'hostile': return coolColorPalette[0]
    default: return neutralColorPalette[0]
  }
}

// Build gradient stops from event friendliness history
const buildGradientStops = (char, totalEvents) => {
  const eventHistory = char.event_friendliness || []
  
  if (eventHistory.length === 0) {
    // No history - use camp color
    const campColor = getCampColor(char, 0)
    return [
      { offset: 0, color: campColor, opacity: 0.3 },
      { offset: 50, color: campColor, opacity: 0.5 },
      { offset: 100, color: campColor, opacity: 0.3 },
    ]
  }
  
  // Calculate gradient stops based on event history
  const stops = []
  
  // Start color based on first_level
  const firstColor = interpolateFriendlyColor(char.first_level || 0)
  stops.push({ offset: 0, color: firstColor, opacity: 0.3 })
  
  // Add stops for each event in history
  eventHistory.forEach((eh, idx) => {
    // Calculate position as percentage (based on time_order relative to total events)
    const position = totalEvents > 1 
      ? (eh.time_order / totalEvents) * 100 
      : 50
    
    // Get color based on cumulative level
    const color = interpolateFriendlyColor(eh.cumulative_level)
    
    stops.push({
      offset: Math.min(95, Math.max(5, position)),
      color,
      opacity: 0.5
    })
  })
  
  // End color based on final cumulative level
  const lastEvent = eventHistory[eventHistory.length - 1]
  const endColor = lastEvent 
    ? interpolateFriendlyColor(lastEvent.cumulative_level)
    : firstColor
  stops.push({ offset: 100, color: endColor, opacity: 0.3 })
  
  // Sort stops by offset and remove duplicates
  stops.sort((a, b) => a.offset - b.offset)
  
  return stops
}

function StoryRibbons({ story }) {
  const svgRef = useRef(null)
  const containerRef = useRef(null)
  const [ribbonData, setRibbonData] = useState(null)
  const [selectedEvent, setSelectedEvent] = useState(null)
  const [hoveredChar, setHoveredChar] = useState(null)
  const [dimensions, setDimensions] = useState({ width: 1200, height: 600 })
  const [loading, setLoading] = useState(true)
  const [legendOpen, setLegendOpen] = useState(false)

  // Load data
  useEffect(() => {
    // Prefer processed data from story object (from backend API)
    if (story?.ribbonData) {
      setRibbonData(story.ribbonData)
      setLoading(false)
      return
    }
    
    // Fallback to loading from file (backward compatibility)
    if (!story?.ribbon_file) return
    
    setLoading(true)
    fetch(`/data/${story.ribbon_file}`)
      .then(res => res.json())
      .then(data => {
        setRibbonData(data)
        setLoading(false)
      })
      .catch(err => {
        console.error('Failed to load ribbon data:', err)
        setLoading(false)
      })
  }, [story])

  // Handle resize
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const { width } = containerRef.current.getBoundingClientRect()
        const height = ribbonData ? Math.max(450, ribbonData.characters.length * 80 + 150) : 500
        setDimensions({ width: Math.max(800, width - 40), height })
      }
    }
    
    updateDimensions()
    window.addEventListener('resize', updateDimensions)
    return () => window.removeEventListener('resize', updateDimensions)
  }, [ribbonData])

  // Main visualization render
  useEffect(() => {
    if (!ribbonData || !svgRef.current) return

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    const { width, height } = dimensions
    const { characters, events, title } = ribbonData
    const margin = { top: 80, right: 60, bottom: 60, left: 160 }
    const innerWidth = width - margin.left - margin.right
    const innerHeight = height - margin.top - margin.bottom

    if (events.length === 0 || characters.length === 0) {
      svg.append('text')
        .attr('x', width / 2)
        .attr('y', height / 2)
        .attr('text-anchor', 'middle')
        .attr('fill', '#6b6b6b')
        .text('No event data available')
      return
    }

    // Sort events by time_order
    const sortedEvents = [...events].filter(e => e.time_order > 0).sort((a, b) => a.time_order - b.time_order)
    if (sortedEvents.length === 0) return

    // Create main group
    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`)

    // Scales
    const xScale = d3.scaleLinear()
      .domain([0, sortedEvents.length - 1])
      .range([0, innerWidth])

    const yScale = d3.scaleBand()
      .domain(characters.map((_, i) => i))
      .range([0, innerHeight])
      .padding(0.3)

    // Increase base ribbon height for wider ribbons
    const ribbonHeight = Math.min(yScale.bandwidth() * 1.1, 45)

    // Helper: find character index by name (fuzzy match)
    const findCharIndex = (name) => {
      return characters.findIndex(c => 
        c.name === name || 
        c.name.includes(name) || 
        name.includes(c.name)
      )
    }

    // Build ribbon path data for each character
    // For each event, calculate Y position based on agent/target role
    const buildRibbonPoints = () => {
      const charPoints = characters.map((char, charIdx) => ({
        char,
        charIdx,
        points: [] // [{x, y, isAgent, event}]
      }))

      // Add start point for each character
      charPoints.forEach((cp, idx) => {
        cp.points.push({
          x: -20,
          y: yScale(idx) + yScale.bandwidth() / 2,
          baseY: yScale(idx) + yScale.bandwidth() / 2,
          isAgent: false,
          event: null
        })
      })

      // Process each event
      sortedEvents.forEach((event, eventIdx) => {
        const x = xScale(eventIdx)
        const agents = event.agents || []
        const targets = event.targets || []
        
        // Find agent and target indices
        const agentIndices = agents.map(a => findCharIndex(a)).filter(i => i !== -1)
        const targetIndices = targets.map(t => findCharIndex(t)).filter(i => i !== -1)
        
        // Calculate anchor Y (average Y of all agents' base positions)
        let anchorY = null
        if (agentIndices.length > 0) {
          anchorY = d3.mean(agentIndices, idx => yScale(idx) + yScale.bandwidth() / 2)
        }

        // Pull strengths
        const agentPullStrength = 0.7  // Agents move 70% toward anchor
        const targetPullStrength = 0.9  // Targets move 90% toward anchor

        // Update each character's position at this event
        charPoints.forEach((cp, charIdx) => {
          const baseY = yScale(charIdx) + yScale.bandwidth() / 2
          let y = baseY
          let isAgent = false
          let isTarget = false
          let isInvolved = false

          if (agentIndices.includes(charIdx)) {
            // Agent: move toward anchor Y (average of all agents)
            isAgent = true
            isInvolved = true
            if (anchorY !== null && agentIndices.length > 1) {
              // Only move if there are multiple agents
              y = baseY + (anchorY - baseY) * agentPullStrength
            } else {
              y = baseY  // Single agent stays at home
            }
          } else if (targetIndices.includes(charIdx) && anchorY !== null) {
            // Target: move toward anchor Y
            isTarget = true
            isInvolved = true
            y = baseY + (anchorY - baseY) * targetPullStrength
          }

          cp.points.push({
            x,
            y,
            baseY,
            isAgent,
            isTarget,
            isInvolved,
            event
          })
        })
      })

      // Add end point for each character
      charPoints.forEach((cp, idx) => {
        cp.points.push({
          x: innerWidth + 20,
          y: yScale(idx) + yScale.bandwidth() / 2,
          baseY: yScale(idx) + yScale.bandwidth() / 2,
          isAgent: false,
          event: null
        })
      })

      return charPoints
    }

    const charRibbonData = buildRibbonPoints()

    // Create ribbon area generator
    // Lower alpha (0.3) makes curves smoother, reducing visual thinning at bends
    const ribbonArea = d3.area()
      .x(d => d.x)
      .y0(d => d.y - ribbonHeight / 2)
      .y1(d => d.y + ribbonHeight / 2)
      .curve(d3.curveCatmullRom.alpha(0.3))

    // Create ribbon line (center path)
    const ribbonLine = d3.line()
      .x(d => d.x)
      .y(d => d.y)
      .curve(d3.curveCatmullRom.alpha(0.3))

    // Add gradient definitions with dynamic color stops based on event friendliness
    const defs = svg.append('defs')
    const totalEvents = sortedEvents.length
    
    characters.forEach((char, idx) => {
      const campColor = getCampColor(char, idx)
      const isHero = char.is_main_hero || char.hero_relationship === 'hero'
      
      // Build gradient stops from event friendliness history
      const gradientStops = isHero 
        ? [
            { offset: 0, color: heroColor, opacity: 0.4 },
            { offset: 50, color: heroColor, opacity: 0.6 },
            { offset: 100, color: heroColor, opacity: 0.4 },
          ]
        : buildGradientStops(char, totalEvents)
      
      // Gradient for ribbon fill (shows friendliness progression)
      const gradient = defs.append('linearGradient')
        .attr('id', `ribbon-gradient-${idx}`)
        .attr('x1', '0%').attr('y1', '0%')
        .attr('x2', '100%').attr('y2', '0%')
      
      gradientStops.forEach(stop => {
        gradient.append('stop')
          .attr('offset', `${stop.offset}%`)
          .attr('stop-color', stop.color)
          .attr('stop-opacity', stop.opacity)
      })
    })

    // Draw background grid
    const gridGroup = g.append('g').attr('class', 'grid')

    // Horizontal grid lines (character lanes)
    gridGroup.selectAll('.grid-h')
      .data(characters)
      .join('line')
      .attr('class', 'grid-h')
      .attr('x1', -20)
      .attr('x2', innerWidth + 20)
      .attr('y1', (_, i) => yScale(i) + yScale.bandwidth() / 2)
      .attr('y2', (_, i) => yScale(i) + yScale.bandwidth() / 2)
      .attr('stroke', '#e5e5e5')
      .attr('stroke-dasharray', '4,4')

    // Vertical grid lines (events)
    gridGroup.selectAll('.grid-v')
      .data(sortedEvents)
      .join('line')
      .attr('class', 'grid-v')
      .attr('x1', (_, i) => xScale(i))
      .attr('x2', (_, i) => xScale(i))
      .attr('y1', -10)
      .attr('y2', innerHeight + 10)
      .attr('stroke', '#f0f0f0')

    // Draw ribbons
    const ribbonsGroup = g.append('g').attr('class', 'ribbons')

    charRibbonData.forEach((charData, idx) => {
      // Camp color for center line (based on hero_relationship and first_level)
      const campColor = getCampColor(charData.char, idx)
      const isHero = charData.char.is_main_hero || charData.char.hero_relationship === 'hero'
      const ribbonG = ribbonsGroup.append('g')
        .attr('class', `ribbon ribbon-${idx} ${isHero ? 'ribbon-hero' : ''}`)
        .attr('data-char-idx', idx)

      // Ribbon fill (area) - uses gradient that shows friendliness progression
      ribbonG.append('path')
        .attr('class', 'ribbon-area')
        .attr('d', ribbonArea(charData.points))
        .attr('fill', `url(#ribbon-gradient-${idx})`)
        .attr('stroke', 'none')

      // Ribbon stroke (center line) - uses CAMP color (stable)
      ribbonG.append('path')
        .attr('class', 'ribbon-line')
        .attr('d', ribbonLine(charData.points))
        .attr('fill', 'none')
        .attr('stroke', campColor)
        .attr('stroke-width', 2.5)
        .attr('stroke-opacity', 0.9)

      // Interaction points (where character is involved)
      // Color the points based on the event's sentiment
      const eventHistory = charData.char.event_friendliness || []
      
      charData.points.forEach((pt, ptIdx) => {
        if (pt.isInvolved && pt.event) {
          // Find the friendliness at this event
          const eventEntry = eventHistory.find(eh => eh.time_order === pt.event.time_order)
          const pointColor = eventEntry 
            ? interpolateFriendlyColor(eventEntry.cumulative_level)
            : campColor
          
          ribbonG.append('circle')
            .attr('class', 'interaction-point')
            .attr('cx', pt.x)
            .attr('cy', pt.y)
            .attr('r', pt.isAgent ? 6 : 4)
            .attr('fill', pt.isAgent ? pointColor : 'white')
            .attr('stroke', pointColor)
            .attr('stroke-width', 2)
            .attr('data-event-idx', ptIdx)
            .style('cursor', 'pointer')
        }
      })

      // Hover behavior for ribbon
      ribbonG
        .style('cursor', 'pointer')
        .on('mouseenter', function() {
          setHoveredChar(charData.char)
          
          // Highlight this ribbon
          d3.select(this).select('.ribbon-area')
            .transition().duration(150)
            .attr('fill-opacity', 1)
          
          d3.select(this).select('.ribbon-line')
            .transition().duration(150)
            .attr('stroke-width', 3)
            .attr('stroke-opacity', 1)

          // Dim other ribbons
          ribbonsGroup.selectAll('.ribbon').filter((_, i) => i !== idx)
            .transition().duration(150)
            .attr('opacity', 0.2)
        })
        .on('mouseleave', function() {
          setHoveredChar(null)
          
          d3.select(this).select('.ribbon-area')
            .transition().duration(150)
            .attr('fill-opacity', 1)
          
          d3.select(this).select('.ribbon-line')
            .transition().duration(150)
            .attr('stroke-width', 2)
            .attr('stroke-opacity', 0.8)

          ribbonsGroup.selectAll('.ribbon')
            .transition().duration(150)
            .attr('opacity', 1)
        })
    })

    // Draw event markers on top
    const eventsGroup = g.append('g').attr('class', 'events-markers')

    sortedEvents.forEach((event, eventIdx) => {
      const x = xScale(eventIdx)
      const eventG = eventsGroup.append('g')
        .attr('class', 'event-marker')
        .attr('transform', `translate(${x}, 0)`)

      // Event number at top
      eventG.append('text')
        .attr('y', -25)
        .attr('text-anchor', 'middle')
        .attr('font-size', '10px')
        .attr('fill', '#999')
        .text(event.time_order)

      // Event type label (rotated)
      eventG.append('text')
        .attr('y', innerHeight + 20)
        .attr('text-anchor', 'start')
        .attr('font-size', '8px')
        .attr('fill', eventTypeColors[event.event_type] || '#666')
        .attr('transform', `rotate(45, 0, ${innerHeight + 20})`)
        .text(event.event_type?.replace(/_/g, ' ').substring(0, 15) || '')

      // Invisible hit area for event hover
      eventG.append('rect')
        .attr('x', -15)
        .attr('y', -10)
        .attr('width', 30)
        .attr('height', innerHeight + 20)
        .attr('fill', 'transparent')
        .style('cursor', 'pointer')
        .on('mouseenter', () => setSelectedEvent(event))
        .on('mouseleave', () => setSelectedEvent(null))
    })

    // Character labels (Y axis)
    const labelsGroup = g.append('g').attr('class', 'char-labels')
    
    characters.forEach((char, idx) => {
      const y = yScale(idx) + yScale.bandwidth() / 2
      const color = getCharacterColor(char, idx)
      const isHero = char.is_main_hero || char.hero_relationship === 'hero'
      const relationship = char.hero_relationship || 'neutral'
      
      const labelG = labelsGroup.append('g')
        .attr('transform', `translate(-10, ${y})`)
        .attr('class', `char-label ${isHero ? 'char-label-hero' : ''}`)

      // Color dot (larger for hero)
      labelG.append('circle')
        .attr('cx', -10)
        .attr('r', isHero ? 8 : 6)
        .attr('fill', color)
        .attr('stroke', isHero ? '#fff' : 'none')
        .attr('stroke-width', isHero ? 2 : 0)

      // Character name
      labelG.append('text')
        .attr('x', -25)
        .attr('text-anchor', 'end')
        .attr('dy', '0.35em')
        .attr('font-family', 'var(--font-chinese), var(--font-serif)')
        .attr('font-size', isHero ? '14px' : '12px')
        .attr('font-weight', isHero ? 'bold' : 'normal')
        .attr('fill', '#333')
        .text(char.name)

      // Relationship badge
      const badgeText = isHero ? '★ Hero' : 
                        relationship === 'friendly' ? 'Friendly' :
                        relationship === 'hostile' ? 'Hostile' : ''
      
      if (badgeText) {
        labelG.append('text')
          .attr('x', -25)
          .attr('y', 14)
          .attr('text-anchor', 'end')
          .attr('font-size', '9px')
          .attr('fill', color)
          .text(badgeText)
      }

      // Archetype (smaller, below relationship)
      labelG.append('text')
        .attr('x', -25)
        .attr('y', badgeText ? 26 : 14)
        .attr('text-anchor', 'end')
        .attr('font-size', '8px')
        .attr('fill', '#aaa')
        .text(char.archetype || '')
    })

    // Title
    svg.append('text')
      .attr('x', margin.left)
      .attr('y', 35)
      .attr('font-family', 'var(--font-chinese), var(--font-serif)')
      .attr('font-size', '18px')
      .attr('fill', '#1a1a1a')
      .text(title || 'Story Ribbons')

    // Subtitle
    svg.append('text')
      .attr('x', margin.left)
      .attr('y', 55)
      .attr('font-size', '11px')
      .attr('fill', '#888')
      .text('Ribbons show character interactions through the narrative')

  }, [ribbonData, dimensions])

  if (loading) {
    return (
      <div className="story-ribbons loading">
        <div className="loading-spinner"></div>
        <p>Loading story events...</p>
      </div>
    )
  }

  return (
    <div className="story-ribbons" ref={containerRef}>
      <div className="ribbons-wrapper">
        <svg 
          ref={svgRef} 
          width={dimensions.width} 
          height={dimensions.height}
          className="ribbons-svg"
        />
      </div>

      {/* Collapsible Legend - Fixed position, outside scrollable wrapper */}
      <div className={`ribbons-legend ${legendOpen ? 'open' : 'collapsed'}`}>
        <button 
          className="legend-toggle"
          onClick={() => setLegendOpen(!legendOpen)}
          title={legendOpen ? 'Hide legend' : 'Show legend'}
        >
          <span className="toggle-icon">{legendOpen ? '✕' : '?'}</span>
          <span className="toggle-text">{legendOpen ? 'Hide' : 'Legend'}</span>
        </button>
        
        {legendOpen && (
          <div className="legend-content">
            <div className="legend-row">
              <div className="legend-section">
                <h4>Character Camp</h4>
                <div className="legend-items compact">
                  <div className="legend-item">
                    <span className="legend-dot-large" style={{ background: heroColor }}></span>
                    <span>Hero (center)</span>
                  </div>
                  <div className="legend-item">
                    <div 
                      className="legend-mini-gradient"
                      style={{ 
                        background: 'linear-gradient(to right, #aeb6bf, #f5b041, #c0392b)',
                        width: '40px',
                        height: '10px',
                        borderRadius: '2px'
                      }}
                    ></div>
                    <span>Friendly (above)</span>
                  </div>
                  <div className="legend-item">
                    <div 
                      className="legend-mini-gradient"
                      style={{ 
                        background: 'linear-gradient(to right, #1a5276, #5dade2, #aeb6bf)',
                        width: '40px',
                        height: '10px',
                        borderRadius: '2px'
                      }}
                    ></div>
                    <span>Hostile (below)</span>
                  </div>
                </div>
              </div>
              <div className="legend-section">
                <h4>Sentiment Heatmap</h4>
                <div className="legend-items compact">
                  <div className="legend-item heatmap-bar-container">
                    <div 
                      className="heatmap-gradient-bar"
                      style={{ 
                        background: 'linear-gradient(to right, #1a5276, #5dade2, #aeb6bf, #f5b041, #c0392b)',
                        width: '100%',
                        height: '20px',
                        borderRadius: '4px',
                        border: '1px solid #ddd'
                      }}
                    ></div>
                    <div className="heatmap-labels">
                      <span>Hostile</span>
                      <span>Neutral</span>
                      <span>Friendly</span>
                    </div>
                  </div>
                  <div className="legend-item">
                    <span className="legend-line" style={{ background: '#333' }}></span>
                    <span>Center = Camp</span>
                  </div>
                </div>
              </div>
            </div>
            <div className="legend-row">
              <div className="legend-section">
                <h4>Interaction</h4>
                <div className="legend-items compact horizontal">
                  <div className="legend-item">
                    <span className="legend-dot-small" style={{ background: '#333' }}></span>
                    <span>Agent</span>
                  </div>
                  <div className="legend-item">
                    <span className="legend-dot-hollow"></span>
                    <span>Target</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {hoveredChar && (
          <div className="legend-section hovered-char">
            <p className="char-name">{hoveredChar.name}</p>
            <span className="char-info">
              {hoveredChar.archetype && <span>{hoveredChar.archetype}</span>}
              {hoveredChar.hero_relationship && (
                <span className="char-relationship" style={{ color: getCharacterColor(hoveredChar, 0) }}>
                  {hoveredChar.hero_relationship === 'hero' ? '★ Hero' :
                   hoveredChar.hero_relationship === 'friendly' ? 'Friendly' :
                   hoveredChar.hero_relationship === 'hostile' ? 'Hostile' : 'Neutral'}
                </span>
              )}
            </span>
          </div>
        )}
      </div>

      {/* Selected event info */}
      {selectedEvent && (
        <div className="event-info-panel">
          <div className="event-info-header">
            <span 
              className="event-type-badge" 
              style={{ background: eventTypeColors[selectedEvent.event_type] || '#666' }}
            >
              {selectedEvent.event_type?.replace(/_/g, ' ') || 'Event'}
            </span>
            <span className="event-time">#{selectedEvent.time_order}</span>
          </div>
          
          <p className="event-description">{selectedEvent.description}</p>
          
          <div className="event-participants">
            {selectedEvent.agents?.length > 0 && (
              <div className="participant-group">
                <span className="participant-label">Agents:</span>
                <span className="participant-names">{selectedEvent.agents.join(', ')}</span>
              </div>
            )}
            {selectedEvent.targets?.length > 0 && (
              <div className="participant-group">
                <span className="participant-label">Targets:</span>
                <span className="participant-names">{selectedEvent.targets.join(', ')}</span>
              </div>
            )}
          </div>

          {selectedEvent.text_excerpt && (
            <div className="event-excerpt">
              <p>"{selectedEvent.text_excerpt}"</p>
            </div>
          )}
        </div>
      )}

      <div className="ribbons-controls">
        <p className="hint">
          <span className="hint-icon">💡</span>
          Hover ribbons for characters • Hover events for details
        </p>
      </div>
    </div>
  )
}

export default StoryRibbons
