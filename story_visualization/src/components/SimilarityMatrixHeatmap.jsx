import React, { useEffect, useRef } from 'react'
import * as d3 from 'd3'
import './Visualization.css'

export default function SimilarityMatrixHeatmap({ 
  similarityMatrix, 
  groundTruthBoundaries = [],
  contextWindow = null,
  title = "Cosine Similarity Matrix"
}) {
  const svgRef = useRef(null)
  const containerRef = useRef(null)

  useEffect(() => {
    if (!similarityMatrix || !similarityMatrix.length) return

    const container = containerRef.current
    const svg = d3.select(svgRef.current)
    svg.selectAll("*").remove() // Clear previous content

    const margin = { top: 60, right: 80, bottom: 60, left: 80 }
    const width = container.clientWidth - margin.left - margin.right
    const height = width // Square matrix
    const size = similarityMatrix.length

    // Create main group
    const g = svg
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`)

    // Color scale (similar to magma colormap)
    const colorScale = d3.scaleSequential()
      .domain([0, 1])
      .interpolator(d3.interpolateMagma)

    // Create heatmap cells
    const cellSize = width / size

    g.selectAll(".cell")
      .data(similarityMatrix.flatMap((row, i) => row.map((val, j) => ({ i, j, value: val }))))
      .enter()
      .append("rect")
      .attr("class", "cell")
      .attr("x", d => d.j * cellSize)
      .attr("y", d => d.i * cellSize)
      .attr("width", cellSize)
      .attr("height", cellSize)
      .attr("fill", d => colorScale(d.value))
      .attr("stroke", "none")
      .attr("opacity", d => {
        // If contextWindow is set, reduce opacity for cells outside the context window
        if (contextWindow !== null && contextWindow !== undefined) {
          const distance = Math.abs(d.i - d.j)
          if (distance > contextWindow) {
            // Reduce opacity for cells outside context window (fade to 30% opacity)
            return 0.3
          }
        }
        // Full opacity for cells within context window or if contextWindow is not set
        return 1.0
      })

    // Draw ground truth boundaries
    groundTruthBoundaries.forEach((boundary, idx) => {
      if (boundary >= 0 && boundary < size) {
        // Horizontal line
        g.append("line")
          .attr("x1", 0)
          .attr("x2", width)
          .attr("y1", boundary * cellSize)
          .attr("y2", boundary * cellSize)
          .attr("stroke", "cyan")
          .attr("stroke-width", 1)
          .attr("stroke-dasharray", "4,4")
          .attr("opacity", 0.7)
          .attr("class", idx === 0 ? "gt-boundary" : null)
        
        // Vertical line
        g.append("line")
          .attr("x1", boundary * cellSize)
          .attr("x2", boundary * cellSize)
          .attr("y1", 0)
          .attr("y2", height)
          .attr("stroke", "cyan")
          .attr("stroke-width", 1)
          .attr("stroke-dasharray", "4,4")
          .attr("opacity", 0.7)
      }
    })

    // Add legend for ground truth
    if (groundTruthBoundaries.length > 0) {
      g.append("line")
        .attr("x1", width - 100)
        .attr("x2", width - 60)
        .attr("y1", -40)
        .attr("y2", -40)
        .attr("stroke", "cyan")
        .attr("stroke-width", 2)
        .attr("stroke-dasharray", "4,4")
      
      g.append("text")
        .attr("x", width - 50)
        .attr("y", -37)
        .attr("fill", "cyan")
        .attr("font-size", "12px")
        .text("Ground Truth")
    }

    // Add color scale legend
    const legendWidth = 20
    const legendHeight = height

    const legendScale = d3.scaleLinear()
      .domain([1, 0])
      .range([0, legendHeight])

    const legendAxis = d3.axisRight(legendScale)
      .ticks(5)
      .tickFormat(d3.format(".2f"))

    const legend = g.append("g")
      .attr("transform", `translate(${width + 20}, 0)`)

    legend.selectAll(".legend-cell")
      .data(d3.range(legendHeight))
      .enter()
      .append("rect")
      .attr("class", "legend-cell")
      .attr("x", 0)
      .attr("y", d => d)
      .attr("width", legendWidth)
      .attr("height", 1)
      .attr("fill", d => colorScale(1 - d / legendHeight))

    legend.append("g")
      .attr("class", "legend-axis")
      .call(legendAxis)

    legend.append("text")
      .attr("x", legendWidth / 2)
      .attr("y", -20)
      .attr("text-anchor", "middle")
      .attr("font-size", "12px")
      .attr("fill", "#333")
      .text("Similarity")

    // Add title
    svg.append("text")
      .attr("x", (width + margin.left + margin.right) / 2)
      .attr("y", 30)
      .attr("text-anchor", "middle")
      .attr("font-size", "16px")
      .attr("font-weight", "bold")
      .attr("fill", "#333")
      .text(title)

    // Add axis labels
    g.append("text")
      .attr("x", width / 2)
      .attr("y", height + 50)
      .attr("text-anchor", "middle")
      .attr("font-size", "12px")
      .attr("fill", "#666")
      .text("Sentence Index")

    g.append("text")
      .attr("transform", "rotate(-90)")
      .attr("x", -height / 2)
      .attr("y", -50)
      .attr("text-anchor", "middle")
      .attr("font-size", "12px")
      .attr("fill", "#666")
      .text("Sentence Index")

  }, [similarityMatrix, groundTruthBoundaries, contextWindow, title])

  if (!similarityMatrix || !similarityMatrix.length) {
    return (
      <div className="visualization-placeholder">
        <p>No similarity matrix data available</p>
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
