import React, { useEffect, useRef } from 'react'
import * as d3 from 'd3'
import './Visualization.css'

export default function GraphSegSMChart({ 
  graph = null,
  threshold = 0.7,
  cliques = null,
  predictedBoundaries = [],
  title = "GraphSegSM Structure"
}) {
  const svgRef = useRef(null)
  const containerRef = useRef(null)
  const simulationRef = useRef(null)

  useEffect(() => {
    if (!graph || !graph.nodes || !graph.edges) return

    const container = containerRef.current
    const svg = d3.select(svgRef.current)
    svg.selectAll("*").remove()

    // Stop previous simulation if exists
    if (simulationRef.current) {
      simulationRef.current.stop()
    }

    const margin = { top: 60, right: 80, bottom: 60, left: 80 }
    const width = container.clientWidth - margin.left - margin.right
    const height = Math.max(400, width * 0.8)

    const g = svg
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`)

    // Prepare nodes and links
    const nodes = graph.nodes.map(nodeId => ({
      id: nodeId,
      label: `S${nodeId}`,
      isBoundary: predictedBoundaries.includes(nodeId)
    }))

    // Create a map for quick node lookup
    const nodeMap = new Map(nodes.map(node => [node.id, node]))

    const links = graph.edges.map(edge => {
      const sourceNode = nodeMap.get(edge[0])
      const targetNode = nodeMap.get(edge[1])
      return {
        source: sourceNode || edge[0],
        target: targetNode || edge[1]
      }
    })

    // Initialize node positions within bounds
    const padding = 30
    nodes.forEach(node => {
      // Random initial position within bounds
      if (!node.x && !node.y) {
        node.x = padding + Math.random() * (width - 2 * padding)
        node.y = padding + Math.random() * (height - 2 * padding)
      }
    })

    // Create force simulation
    const simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id(d => d.id).distance(50))
      .force("charge", d3.forceManyBody().strength(-200))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(20))
    
    // Store simulation reference
    simulationRef.current = simulation

    // Create color scale for cliques
    let cliqueColors = {}
    if (cliques && cliques.length > 0) {
      const colorScale = d3.scaleOrdinal(d3.schemeCategory10)
      cliques.forEach((clique, idx) => {
        clique.forEach(nodeId => {
          if (!cliqueColors[nodeId] || clique.length > (cliqueColors[nodeId].size || 0)) {
            cliqueColors[nodeId] = {
              color: colorScale(idx),
              size: clique.length
            }
          }
        })
      })
    }

    // Draw links
    const link = g.append("g")
      .attr("class", "links")
      .selectAll("line")
      .data(links)
      .enter()
      .append("line")
      .attr("stroke", "#999")
      .attr("stroke-opacity", 0.6)
      .attr("stroke-width", 1.5)

    // Draw nodes
    const node = g.append("g")
      .attr("class", "nodes")
      .selectAll("circle")
      .data(nodes)
      .enter()
      .append("circle")
      .attr("r", d => d.isBoundary ? 8 : 6)
      .attr("fill", d => {
        if (d.isBoundary) return "#ff4444"
        if (cliqueColors[d.id]) return cliqueColors[d.id].color
        return "#999"
      })
      .attr("stroke", d => d.isBoundary ? "#cc0000" : "#fff")
      .attr("stroke-width", d => d.isBoundary ? 2 : 1.5)
      .call(d3.drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended))

    // Add labels
    const labels = g.append("g")
      .attr("class", "labels")
      .selectAll("text")
      .data(nodes)
      .enter()
      .append("text")
      .attr("text-anchor", "middle")
      .attr("dy", -12)
      .attr("font-size", "10px")
      .attr("fill", "#333")
      .text(d => d.label)

    // Tooltip
    const tooltip = d3.select("body").append("div")
      .attr("class", "graph-tooltip")
      .style("opacity", 0)
      .style("position", "absolute")
      .style("background", "rgba(0, 0, 0, 0.8)")
      .style("color", "white")
      .style("padding", "8px")
      .style("border-radius", "4px")
      .style("font-size", "12px")
      .style("pointer-events", "none")
      .style("z-index", 1000)

    node.on("mouseover", function(event, d) {
        let tooltipText = `Sentence ${d.id}`
        if (d.isBoundary) {
          tooltipText += " (Boundary)"
        }
        if (cliqueColors[d.id]) {
          const cliqueSize = cliqueColors[d.id].size
          tooltipText += `<br/>Clique size: ${cliqueSize}`
        }
        tooltip.transition()
          .duration(200)
          .style("opacity", 1)
        tooltip.html(tooltipText)
          .style("left", (event.pageX + 10) + "px")
          .style("top", (event.pageY - 10) + "px")
      })
      .on("mouseout", function() {
        tooltip.transition()
          .duration(200)
          .style("opacity", 0)
      })

    // Update positions on simulation tick with boundary constraints
    simulation.on("tick", () => {
      // Constrain node positions to stay within bounds (with padding)
      const padding = 30
      // Legend area: bottom-left, exclude from node placement
      const legendX = 20
      const legendY = height - 200
      const legendWidth = 180
      const legendHeight = 200
      
      nodes.forEach(d => {
        // Only constrain if not fixed by drag
        if (d.fx === null && d.fy === null) {
          // Constrain x: avoid left side where legend is (if in legend y-range)
          let minX = padding
          if (d.y >= legendY - 20 && d.y <= legendY + legendHeight) {
            // If in legend y-range, exclude legend area
            minX = Math.max(minX, legendX + legendWidth + padding)
          }
          d.x = Math.max(minX, Math.min(width - padding, d.x))
          
          // Constrain y: avoid bottom where legend is (if in legend x-range)
          let maxY = height - padding
          if (d.x >= legendX - 20 && d.x <= legendX + legendWidth) {
            // If in legend x-range, exclude legend area
            maxY = Math.min(maxY, legendY - padding)
          }
          d.y = Math.max(padding, Math.min(maxY, d.y))
        } else {
          // If fixed, still ensure it's within bounds
          let minX = padding
          if ((d.y || d.fy) >= legendY - 20 && (d.y || d.fy) <= legendY + legendHeight) {
            minX = Math.max(minX, legendX + legendWidth + padding)
          }
          d.x = Math.max(minX, Math.min(width - padding, d.x || d.fx))
          
          let maxY = height - padding
          if ((d.x || d.fx) >= legendX - 20 && (d.x || d.fx) <= legendX + legendWidth) {
            maxY = Math.min(maxY, legendY - padding)
          }
          d.y = Math.max(padding, Math.min(maxY, d.y || d.fy))
        }
      })

      link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y)

      node
        .attr("cx", d => d.x)
        .attr("cy", d => d.y)

      labels
        .attr("x", d => d.x)
        .attr("y", d => d.y)
    })

    // Drag functions
    function dragstarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart()
      d.fx = d.x
      d.fy = d.y
    }

    function dragged(event, d) {
      // Constrain dragged position to bounds, excluding legend area
      const padding = 30
      const legendX = 20
      const legendY = height - 200
      const legendWidth = 180
      const legendHeight = 200
      
      let minX = padding
      if (event.y >= legendY - 20 && event.y <= legendY + legendHeight) {
        // If in legend y-range, exclude legend area
        minX = Math.max(minX, legendX + legendWidth + padding)
      }
      
      let maxY = height - padding
      if (event.x >= legendX - 20 && event.x <= legendX + legendWidth) {
        // If in legend x-range, exclude legend area
        maxY = Math.min(maxY, legendY - padding)
      }
      
      d.fx = Math.max(minX, Math.min(width - padding, event.x))
      d.fy = Math.max(padding, Math.min(maxY, event.y))
    }

    function dragended(event, d) {
      if (!event.active) simulation.alphaTarget(0)
      d.fx = null
      d.fy = null
    }

    // Add title
    svg.append("text")
      .attr("x", (width + margin.left + margin.right) / 2)
      .attr("y", 30)
      .attr("text-anchor", "middle")
      .attr("font-size", "16px")
      .attr("font-weight", "bold")
      .attr("fill", "#333")
      .text(title)

    // Add legend (positioned at bottom-left to avoid node overlap)
    const legend = g.append("g")
      .attr("transform", `translate(20, ${height - 200})`)

    let legendY = 0

    // Legend: normal node
    legend.append("circle")
      .attr("cx", 10)
      .attr("cy", legendY)
      .attr("r", 6)
      .attr("fill", "#999")
      .attr("stroke", "#fff")
      .attr("stroke-width", 1.5)
    
    legend.append("text")
      .attr("x", 25)
      .attr("y", legendY + 4)
      .attr("font-size", "11px")
      .text("Sentence Node")
    
    legendY += 25

    // Legend: boundary node
    if (predictedBoundaries.length > 0) {
      legend.append("circle")
        .attr("cx", 10)
        .attr("cy", legendY)
        .attr("r", 8)
        .attr("fill", "#ff4444")
        .attr("stroke", "#cc0000")
        .attr("stroke-width", 2)
      
      legend.append("text")
        .attr("x", 25)
        .attr("y", legendY + 4)
        .attr("font-size", "11px")
        .text("Boundary Node")
      
      legendY += 25
    }

    // Legend: edge
    legend.append("line")
      .attr("x1", 6)
      .attr("x2", 14)
      .attr("y1", legendY)
      .attr("y2", legendY)
      .attr("stroke", "#999")
      .attr("stroke-opacity", 0.6)
      .attr("stroke-width", 1.5)
    
    legend.append("text")
      .attr("x", 25)
      .attr("y", legendY + 4)
      .attr("font-size", "11px")
      .text(`Similarity > ${threshold.toFixed(2)}`)
    
    legendY += 25

    // Legend: clique coloring
    if (cliques && cliques.length > 0) {
      legend.append("text")
        .attr("x", 0)
        .attr("y", legendY)
        .attr("font-size", "10px")
        .attr("font-weight", "bold")
        .text("Cliques:")
      
      legendY += 15

      const uniqueCliqueSizes = [...new Set(cliques.map(c => c.length))].sort((a, b) => b - a).slice(0, 3)
      uniqueCliqueSizes.forEach((size, idx) => {
        const colorScale = d3.scaleOrdinal(d3.schemeCategory10)
        const cliqueIdx = cliques.findIndex(c => c.length === size)
        
        legend.append("circle")
          .attr("cx", 10)
          .attr("cy", legendY)
          .attr("r", 6)
          .attr("fill", colorScale(cliqueIdx))
        
        legend.append("text")
          .attr("x", 25)
          .attr("y", legendY + 4)
          .attr("font-size", "11px")
          .text(`Clique size ${size}`)
        
        legendY += 20
      })
    }

    // Add info text
    g.append("text")
      .attr("x", width / 2)
      .attr("y", height + 40)
      .attr("text-anchor", "middle")
      .attr("font-size", "12px")
      .attr("fill", "#666")
      .text(`Graph: ${nodes.length} nodes, ${links.length} edges`)

    // Cleanup function
    return () => {
      tooltip.remove()
      if (simulationRef.current) {
        simulationRef.current.stop()
        simulationRef.current = null
      }
    }

  }, [graph, threshold, cliques, predictedBoundaries, title])

  if (!graph || !graph.nodes || !graph.edges) {
    return (
      <div className="visualization-placeholder">
        <p>No graph data available</p>
      </div>
    )
  }

  return (
    <div className="visualization-container">
      <div ref={containerRef} className="visualization-svg-container">
        <svg ref={svgRef}></svg>
      </div>
    </div>
  )
}
