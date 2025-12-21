import React, { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'
import './StoryRibbons.css'

// Color schemes
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

const sentimentColors = {
  'positive': '#40916c',
  'negative': '#c1121f',
  'neutral': '#6b6b6b',
  'romantic': '#e63946',
  'fearful': '#7209b7',
  'hostile': '#370617',
}

const characterColors = d3.scaleOrdinal()
  .range(['#e63946', '#40916c', '#219ebc', '#7209b7', '#d4a373', '#f77f00', '#06d6a0', '#ff006e', '#118ab2', '#8338ec'])

function StoryRibbons({ story }) {
  const svgRef = useRef(null)
  const containerRef = useRef(null)
  const [ribbonData, setRibbonData] = useState(null)
  const [selectedEvent, setSelectedEvent] = useState(null)
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 })
  const [loading, setLoading] = useState(true)
  const [viewMode, setViewMode] = useState('timeline') // 'timeline' or 'swimlane'

  // Load data
  useEffect(() => {
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
        setDimensions({ 
          width: width - 40, 
          height: Math.max(500, ribbonData ? 100 + ribbonData.characters.length * 80 + 200 : 600)
        })
      }
    }
    
    updateDimensions()
    window.addEventListener('resize', updateDimensions)
    return () => window.removeEventListener('resize', updateDimensions)
  }, [ribbonData])

  // Render visualization
  useEffect(() => {
    if (!ribbonData || !svgRef.current) return

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    const { width, height } = dimensions
    const { characters, events, title } = ribbonData
    const margin = { top: 60, right: 40, bottom: 80, left: 150 }
    const innerWidth = width - margin.left - margin.right
    const innerHeight = height - margin.top - margin.bottom

    if (events.length === 0) {
      svg.append('text')
        .attr('x', width / 2)
        .attr('y', height / 2)
        .attr('text-anchor', 'middle')
        .attr('fill', '#6b6b6b')
        .text('No event data available')
      return
    }

    // Create main group
    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`)

    // Scales
    const timeScale = d3.scaleLinear()
      .domain([1, d3.max(events, d => d.time_order) || 1])
      .range([0, innerWidth])

    const characterScale = d3.scaleBand()
      .domain(characters.map(c => c.name))
      .range([0, innerHeight])
      .padding(0.3)

    // Add background grid
    const gridGroup = g.append('g').attr('class', 'grid')

    // Vertical grid lines (time)
    const timeExtent = d3.max(events, d => d.time_order) || 1
    const tickCount = Math.min(timeExtent, 20)
    
    gridGroup.selectAll('.grid-line-v')
      .data(d3.range(1, timeExtent + 1))
      .join('line')
      .attr('class', 'grid-line-v')
      .attr('x1', d => timeScale(d))
      .attr('x2', d => timeScale(d))
      .attr('y1', -20)
      .attr('y2', innerHeight + 20)
      .attr('stroke', '#e0ddd5')
      .attr('stroke-dasharray', '3,3')

    // Horizontal grid lines (characters)
    gridGroup.selectAll('.grid-line-h')
      .data(characters)
      .join('line')
      .attr('class', 'grid-line-h')
      .attr('x1', -20)
      .attr('x2', innerWidth + 20)
      .attr('y1', d => characterScale(d.name) + characterScale.bandwidth() / 2)
      .attr('y2', d => characterScale(d.name) + characterScale.bandwidth() / 2)
      .attr('stroke', '#e0ddd5')

    // Character labels (Y axis)
    const characterLabels = g.append('g')
      .attr('class', 'character-labels')
      .attr('transform', 'translate(-10, 0)')

    characterLabels.selectAll('.character-label')
      .data(characters)
      .join('g')
      .attr('class', 'character-label')
      .attr('transform', d => `translate(0, ${characterScale(d.name) + characterScale.bandwidth() / 2})`)
      .each(function(d, i) {
        const group = d3.select(this)
        
        // Character dot
        group.append('circle')
          .attr('r', 8)
          .attr('cx', -20)
          .attr('fill', characterColors(i))

        // Character name
        group.append('text')
          .attr('text-anchor', 'end')
          .attr('dy', '0.35em')
          .attr('x', -35)
          .attr('font-family', 'var(--font-chinese), var(--font-serif)')
          .attr('font-size', '13px')
          .attr('fill', '#1a1a1a')
          .text(d.name)

        // Archetype badge
        group.append('text')
          .attr('text-anchor', 'end')
          .attr('dy', '1.8em')
          .attr('x', -35)
          .attr('font-size', '9px')
          .attr('fill', '#999')
          .text(d.archetype || '')
      })

    // Time axis
    const timeAxis = g.append('g')
      .attr('class', 'time-axis')
      .attr('transform', `translate(0, ${innerHeight + 30})`)

    timeAxis.append('text')
      .attr('x', innerWidth / 2)
      .attr('y', 35)
      .attr('text-anchor', 'middle')
      .attr('font-size', '12px')
      .attr('fill', '#666')
      .text('Story Timeline →')

    // Event ribbons/nodes
    const eventGroup = g.append('g').attr('class', 'events')

    // Draw connecting ribbons between characters in same event
    const ribbonPaths = eventGroup.append('g').attr('class', 'ribbons')

    events.forEach((event, eventIndex) => {
      const allParticipants = [...(event.agents || []), ...(event.targets || [])]
      const participantIndices = allParticipants
        .map(name => characters.findIndex(c => 
          c.name === name || c.name.includes(name) || name.includes(c.name)
        ))
        .filter(i => i !== -1)
        .sort((a, b) => a - b)

      if (participantIndices.length > 1) {
        // Draw ribbon connecting all participants
        const x = timeScale(event.time_order)
        const yMin = characterScale(characters[participantIndices[0]].name) + characterScale.bandwidth() / 2
        const yMax = characterScale(characters[participantIndices[participantIndices.length - 1]].name) + characterScale.bandwidth() / 2

        ribbonPaths.append('rect')
          .attr('class', 'event-ribbon')
          .attr('x', x - 3)
          .attr('y', yMin)
          .attr('width', 6)
          .attr('height', yMax - yMin)
          .attr('fill', eventTypeColors[event.event_type] || eventTypeColors['OTHER'])
          .attr('opacity', 0.3)
          .attr('rx', 3)
      }
    })

    // Draw event nodes
    const eventNodes = eventGroup.selectAll('.event-node')
      .data(events)
      .join('g')
      .attr('class', 'event-node')
      .attr('transform', d => `translate(${timeScale(d.time_order)}, 0)`)

    // For each event, draw dots for each participating character
    eventNodes.each(function(event, eventIndex) {
      const group = d3.select(this)
      const allParticipants = [...new Set([...(event.agents || []), ...(event.targets || [])])]
      
      allParticipants.forEach(participant => {
        const charIndex = characters.findIndex(c => 
          c.name === participant || c.name.includes(participant) || participant.includes(c.name)
        )
        
        if (charIndex !== -1) {
          const y = characterScale(characters[charIndex].name) + characterScale.bandwidth() / 2
          const isAgent = (event.agents || []).some(a => 
            a === participant || a.includes(participant) || participant.includes(a)
          )

          // Node glow
          group.append('circle')
            .attr('class', 'event-glow')
            .attr('cy', y)
            .attr('r', 14)
            .attr('fill', eventTypeColors[event.event_type] || eventTypeColors['OTHER'])
            .attr('opacity', 0.15)

          // Main node
          group.append('circle')
            .attr('class', 'event-dot')
            .attr('cy', y)
            .attr('r', isAgent ? 10 : 7)
            .attr('fill', eventTypeColors[event.event_type] || eventTypeColors['OTHER'])
            .attr('stroke', isAgent ? '#fff' : 'none')
            .attr('stroke-width', isAgent ? 2 : 0)
            .attr('cursor', 'pointer')
            .attr('data-event-id', event.id)
        }
      })

      // Event type label (show on top of the first character involved)
      const firstParticipant = allParticipants[0]
      if (firstParticipant) {
        const charIndex = characters.findIndex(c => 
          c.name === firstParticipant || c.name.includes(firstParticipant) || firstParticipant.includes(c.name)
        )
        if (charIndex !== -1) {
          const y = characterScale(characters[charIndex].name)
          
          group.append('text')
            .attr('class', 'event-type-label')
            .attr('y', y - 15)
            .attr('text-anchor', 'middle')
            .attr('font-size', '8px')
            .attr('fill', eventTypeColors[event.event_type] || '#666')
            .attr('opacity', 0)
            .text(event.event_type?.replace(/_/g, ' ') || 'Event')
        }
      }
    })

    // Interaction overlay
    eventNodes
      .on('mouseenter', function(mouseEvent, d) {
        d3.select(this).selectAll('.event-dot')
          .transition()
          .duration(150)
          .attr('r', function() {
            const current = d3.select(this).attr('r')
            return parseFloat(current) + 3
          })

        d3.select(this).selectAll('.event-glow')
          .transition()
          .duration(150)
          .attr('r', 20)
          .attr('opacity', 0.3)

        d3.select(this).selectAll('.event-type-label')
          .transition()
          .duration(150)
          .attr('opacity', 1)

        setSelectedEvent(d)
      })
      .on('mouseleave', function() {
        d3.select(this).selectAll('.event-dot')
          .transition()
          .duration(150)
          .attr('r', function() {
            const current = d3.select(this).attr('r')
            return parseFloat(current) - 3
          })

        d3.select(this).selectAll('.event-glow')
          .transition()
          .duration(150)
          .attr('r', 14)
          .attr('opacity', 0.15)

        d3.select(this).selectAll('.event-type-label')
          .transition()
          .duration(150)
          .attr('opacity', 0)

        setSelectedEvent(null)
      })

    // Title
    svg.append('text')
      .attr('x', margin.left)
      .attr('y', 30)
      .attr('font-family', 'var(--font-chinese), var(--font-serif)')
      .attr('font-size', '16px')
      .attr('fill', '#1a1a1a')
      .text(`${title} - Story Ribbon`)

  }, [ribbonData, dimensions, viewMode])

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
      <div className="ribbons-header">
        <h2>{story?.title || 'Story Timeline'}</h2>
        <p className="ribbons-subtitle">
          Visual timeline of narrative events and character involvement
        </p>
      </div>

      <div className="ribbons-wrapper">
        <svg 
          ref={svgRef} 
          width={dimensions.width} 
          height={dimensions.height}
          className="ribbons-svg"
        />

        {/* Legend */}
        <div className="ribbons-legend">
          <div className="legend-section">
            <h4>Event Types</h4>
            <div className="legend-items">
              {Object.entries(eventTypeColors).slice(0, 8).map(([type, color]) => (
                <div key={type} className="legend-item">
                  <span className="legend-dot" style={{ background: color }}></span>
                  <span className="legend-label">{type.replace(/_/g, ' ')}</span>
                </div>
              ))}
            </div>
          </div>
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

            {selectedEvent.relationship_level1 && (
              <div className="event-metadata">
                <span className="metadata-item">
                  <strong>Relationship:</strong> {selectedEvent.relationship_level1}
                </span>
                {selectedEvent.sentiment && (
                  <span 
                    className="sentiment-badge"
                    style={{ background: sentimentColors[selectedEvent.sentiment] || '#666' }}
                  >
                    {selectedEvent.sentiment}
                  </span>
                )}
              </div>
            )}

            {selectedEvent.text_excerpt && (
              <div className="event-excerpt">
                <p>"{selectedEvent.text_excerpt}"</p>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="ribbons-controls">
        <p className="hint">
          <span className="hint-icon">💡</span>
          Hover over event nodes to see details • Larger dots = Agents • Smaller dots = Targets
        </p>
      </div>
    </div>
  )
}

export default StoryRibbons

