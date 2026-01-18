import React, { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'
import './CharacterGraph.css'

// Color mapping for archetypes (16 types from character_arctypes.md)
const archetypeColors = {
  // Core protagonists
  'Hero': '#e63946',           // Vermillion red - central figure
  'Sidekick/Helper': '#40916c', // Jade green - supportive
  'Sidekick': '#40916c',        // Alias
  'Helper': '#40916c',          // Alias
  
  // Antagonists & dark figures
  'Villain': '#370617',        // Dark crimson - evil
  'Shadow': '#4a4a4a',         // Dark gray - dark reflection
  
  // Guides & wisdom
  'Mentor': '#7209b7',         // Purple - wisdom
  'Mother': '#f4a261',         // Warm orange - nurturing
  'Guardian': '#219ebc',       // Azure blue - protective
  
  // Neutral & common
  'Everyman': '#6b7280',       // Gray - ordinary
  'Damsel': '#ec4899',         // Pink - innocence
  'Lover': '#f472b6',          // Light pink - romantic
  
  // Chaotic & cunning
  'Trickster': '#f77f00',      // Orange - mischief
  'Outlaw': '#78350f',         // Brown - independence
  'Rebel': '#dc2626',          // Bright red - revolutionary
  
  // Authority & narrative
  'Ruler': '#7c3aed',          // Violet - power
  'Herald': '#d4a373',         // Gold - announcement
  'Scapegoat': '#64748b',      // Slate - blamed
  
  // Fallback
  'Other': '#9ca3af',          // Light gray
  '': '#9ca3af',               // Empty archetype
}

// Color mapping for relationship types (from relationship.csv - Level 1)
const relationshipColors = {
  'Family & Kinship': '#d4a373',   // Gold
  'Romance': '#e63946',            // Red
  'Hierarchy': '#7209b7',          // Purple
  'Social & Alliance': '#219ebc',  // Blue
  'Adversarial': '#370617',        // Dark crimson
  'Neutral': '#9ca3af',            // Gray
  'Unknown': '#6b7280',            // Fallback gray
}

// Color mapping for sentiments
const sentimentColors = {
  'positive': '#40916c',
  'negative': '#c1121f',
  'neutral': '#6b6b6b',
  'romantic': '#e63946',
  'fearful': '#7209b7',
  'hostile': '#370617',
}

function CharacterGraph({ story }) {
  const svgRef = useRef(null)
  const containerRef = useRef(null)
  const [graphData, setGraphData] = useState(null)
  const [selectedNode, setSelectedNode] = useState(null)
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 })
  const [loading, setLoading] = useState(true)

  // Load data
  useEffect(() => {
    // Prefer processed data from story object (from backend API)
    if (story?.relationshipData) {
      setGraphData(story.relationshipData)
      setLoading(false)
      return
    }
    
    // Fallback to loading from file (backward compatibility)
    if (!story?.relationship_file) return
    
    setLoading(true)
    fetch(`/data/${story.relationship_file}`)
      .then(res => res.json())
      .then(data => {
        setGraphData(data)
        setLoading(false)
      })
      .catch(err => {
        console.error('Failed to load relationship data:', err)
        setLoading(false)
      })
  }, [story])

  // Handle resize
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const { width, height } = containerRef.current.getBoundingClientRect()
        setDimensions({ width: width - 40, height: Math.max(500, height - 40) })
      }
    }
    
    updateDimensions()
    window.addEventListener('resize', updateDimensions)
    return () => window.removeEventListener('resize', updateDimensions)
  }, [])

  // Render graph
  useEffect(() => {
    if (!graphData || !svgRef.current) return

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    const { width, height } = dimensions
    const { nodes, edges } = graphData

    if (nodes.length === 0) {
      svg.append('text')
        .attr('x', width / 2)
        .attr('y', height / 2)
        .attr('text-anchor', 'middle')
        .attr('fill', '#6b6b6b')
        .text('No character data available')
      return
    }

    // Create container group for zoom
    const g = svg.append('g')
      .attr('class', 'graph-container')

    // Add zoom behavior
    const zoom = d3.zoom()
      .scaleExtent([0.3, 3])
      .on('zoom', (event) => {
        g.attr('transform', event.transform)
      })
    
    svg.call(zoom)

    // Add gradient definitions for edges
    const defs = svg.append('defs')
    
    // Create arrow markers for each relationship type with matching colors
    Object.entries(relationshipColors).forEach(([relType, color]) => {
      const markerId = `arrowhead-${relType.replace(/[^a-zA-Z0-9]/g, '-')}`
      defs.append('marker')
        .attr('id', markerId)
        .attr('viewBox', '0 -4 8 8')
        .attr('refX', 8)
        .attr('refY', 0)
        .attr('markerWidth', 4)
        .attr('markerHeight', 4)
        .attr('orient', 'auto')
        .attr('markerUnits', 'strokeWidth')
        .append('path')
        .attr('d', 'M0,-4L8,0L0,4Z')
        .attr('fill', color)
    })

    // Helper function to get marker id for relationship type
    const getMarkerId = (relType) => {
      const id = `arrowhead-${(relType || 'Unknown').replace(/[^a-zA-Z0-9]/g, '-')}`
      return `url(#${id})`
    }

    // Create force simulation
    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(edges)
        .id(d => d.id)
        .distance(d => 150 - d.weight * 10)
        .strength(0.5))
      .force('charge', d3.forceManyBody()
        .strength(-400)
        .distanceMax(400))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(50))

    // Create edge groups
    const edgeGroup = g.append('g').attr('class', 'edges')
    
    const edges_g = edgeGroup.selectAll('g')
      .data(edges)
      .join('g')
      .attr('class', 'edge-group')

    // Draw edges
    const links = edges_g.append('path')
      .attr('class', 'edge')
      .attr('stroke', d => relationshipColors[d.relationship_type] || relationshipColors['Unknown'])
      .attr('stroke-width', d => Math.max(2, Math.min(d.weight * 1.5 + 1, 6)))
      .attr('stroke-opacity', 0.6)
      .attr('fill', 'none')
      .attr('marker-end', d => getMarkerId(d.relationship_type))

    // Edge labels
    const edgeLabels = edges_g.append('text')
      .attr('class', 'edge-label')
      .attr('text-anchor', 'middle')
      .attr('dy', -5)
      .attr('font-size', '10px')
      .attr('fill', '#666')
      .text(d => d.relationship_type)
      .attr('opacity', 0)

    // Create node groups
    const nodeGroup = g.append('g').attr('class', 'nodes')
    
    const node_g = nodeGroup.selectAll('g')
      .data(nodes)
      .join('g')
      .attr('class', 'node-group')
      .call(d3.drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended))

    // Node circles with glow effect
    node_g.append('circle')
      .attr('class', 'node-glow')
      .attr('r', 28)
      .attr('fill', d => archetypeColors[d.archetype] || archetypeColors['Other'])
      .attr('opacity', 0.2)
      .attr('filter', 'blur(8px)')

    // Main node circle
    node_g.append('circle')
      .attr('class', 'node')
      .attr('r', 22)
      .attr('fill', d => archetypeColors[d.archetype] || archetypeColors['Other'])
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer')

    // Node labels
    node_g.append('text')
      .attr('class', 'node-label')
      .attr('text-anchor', 'middle')
      .attr('dy', 40)
      .attr('font-size', '13px')
      .attr('font-family', 'var(--font-chinese), var(--font-serif)')
      .attr('fill', '#1a1a1a')
      .attr('font-weight', '600')
      .text(d => d.name)

    // Archetype badge
    node_g.append('text')
      .attr('class', 'archetype-badge')
      .attr('text-anchor', 'middle')
      .attr('dy', 55)
      .attr('font-size', '9px')
      .attr('fill', '#666')
      .text(d => d.archetype || 'Other')

    // Hover interactions
    node_g
      .on('mouseenter', function(event, d) {
        d3.select(this).select('.node')
          .transition()
          .duration(200)
          .attr('r', 28)
        
        d3.select(this).select('.node-glow')
          .transition()
          .duration(200)
          .attr('r', 35)
          .attr('opacity', 0.4)

        // Highlight connected edges
        links
          .transition()
          .duration(200)
          .attr('stroke-opacity', e => 
            e.source.id === d.id || e.target.id === d.id ? 1 : 0.1)
          .attr('stroke-width', e => 
            e.source.id === d.id || e.target.id === d.id 
              ? Math.max(3, Math.min(e.weight * 2 + 2, 8)) 
              : Math.max(2, Math.min(e.weight * 1.5 + 1, 6)))

        // Show edge labels for connected edges
        edgeLabels
          .transition()
          .duration(200)
          .attr('opacity', e => 
            e.source.id === d.id || e.target.id === d.id ? 1 : 0)

        // Dim other nodes
        node_g.select('.node')
          .transition()
          .duration(200)
          .attr('opacity', n => {
            if (n.id === d.id) return 1
            const connected = edges.some(e => 
              (e.source.id === d.id && e.target.id === n.id) ||
              (e.target.id === d.id && e.source.id === n.id))
            return connected ? 1 : 0.3
          })

        setSelectedNode(d)
      })
      .on('mouseleave', function() {
        d3.select(this).select('.node')
          .transition()
          .duration(200)
          .attr('r', 22)
        
        d3.select(this).select('.node-glow')
          .transition()
          .duration(200)
          .attr('r', 28)
          .attr('opacity', 0.2)

        links
          .transition()
          .duration(200)
          .attr('stroke-opacity', 0.6)
          .attr('stroke-width', d => Math.max(2, Math.min(d.weight * 1.5 + 1, 6)))

        edgeLabels
          .transition()
          .duration(200)
          .attr('opacity', 0)

        node_g.select('.node')
          .transition()
          .duration(200)
          .attr('opacity', 1)

        setSelectedNode(null)
      })

    // Simulation tick
    const nodeRadius = 22
    const arrowOffset = 8 // Additional offset for arrow head
    
    simulation.on('tick', () => {
      links.attr('d', d => {
        const dx = d.target.x - d.source.x
        const dy = d.target.y - d.source.y
        const dist = Math.sqrt(dx * dx + dy * dy)
        
        if (dist === 0) return ''
        
        // Calculate unit vector
        const ux = dx / dist
        const uy = dy / dist
        
        // Offset start and end points by node radius
        const startX = d.source.x + ux * nodeRadius
        const startY = d.source.y + uy * nodeRadius
        const endX = d.target.x - ux * (nodeRadius + arrowOffset)
        const endY = d.target.y - uy * (nodeRadius + arrowOffset)
        
        // Calculate arc radius based on distance
        const arcDist = Math.sqrt((endX - startX) ** 2 + (endY - startY) ** 2)
        const dr = Math.max(arcDist * 0.8, 50) // Curve the arc
        
        return `M${startX},${startY}A${dr},${dr} 0 0,1 ${endX},${endY}`
      })

      edgeLabels
        .attr('x', d => (d.source.x + d.target.x) / 2)
        .attr('y', d => (d.source.y + d.target.y) / 2)

      node_g.attr('transform', d => `translate(${d.x},${d.y})`)
    })

    // Drag functions
    function dragstarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart()
      d.fx = d.x
      d.fy = d.y
    }

    function dragged(event, d) {
      d.fx = event.x
      d.fy = event.y
    }

    function dragended(event, d) {
      if (!event.active) simulation.alphaTarget(0)
      d.fx = null
      d.fy = null
    }

    // Cleanup
    return () => {
      simulation.stop()
    }
  }, [graphData, dimensions])

  if (loading) {
    return (
      <div className="character-graph loading">
        <div className="loading-spinner"></div>
        <p>Loading character relationships...</p>
      </div>
    )
  }

  return (
    <div className="character-graph" ref={containerRef}>
      <div className="graph-header">
        <h2>{story?.title || 'Character Relationships'}</h2>
        <p className="graph-subtitle">
          Interactive force-directed graph showing character relationships
        </p>
      </div>

      <div className="graph-wrapper">
        <svg 
          ref={svgRef} 
          width={dimensions.width} 
          height={dimensions.height}
          className="graph-svg"
        />

        {/* Legend */}
        <div className="graph-legend">
          <div className="legend-section">
            <h4>Character Types</h4>
            <div className="legend-items legend-grid">
              {[
                'Hero', 'Villain', 'Mentor', 'Sidekick/Helper',
                'Shadow', 'Mother', 'Guardian', 'Trickster',
                'Lover', 'Everyman', 'Damsel', 'Herald',
                'Ruler', 'Rebel', 'Outlaw', 'Scapegoat',
              ].map((type) => (
                <div key={type} className="legend-item">
                  <span className="legend-dot" style={{ background: archetypeColors[type] }}></span>
                  <span className="legend-label">{type}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="legend-section">
            <h4>Relationship Types</h4>
            <div className="legend-items">
              {[
                'Family & Kinship', 'Romance', 'Hierarchy',
                'Social & Alliance', 'Adversarial', 'Neutral',
              ].map((type) => (
                <div key={type} className="legend-item">
                  <span className="legend-line" style={{ background: relationshipColors[type] }}></span>
                  <span className="legend-label">{type}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Selected node info */}
        {selectedNode && (
          <div className="node-info-panel">
            <h4>{selectedNode.name}</h4>
            <p className="node-archetype">{selectedNode.archetype || 'Other'}</p>
            {selectedNode.alias && (
              <p className="node-alias">Also known as: {selectedNode.alias}</p>
            )}
            {graphData && (
              <p className="node-connections">
                {graphData.edges.filter(e => 
                  e.source.id === selectedNode.id || e.target.id === selectedNode.id
                ).length} connections
              </p>
            )}
          </div>
        )}
      </div>

      <div className="graph-controls">
        <p className="hint">
          <span className="hint-icon">💡</span>
          Drag nodes to reposition • Scroll to zoom • Hover for details
        </p>
      </div>
    </div>
  )
}

export default CharacterGraph

