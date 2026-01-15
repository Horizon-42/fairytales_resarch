import React, { useEffect, useRef } from 'react'
import * as d3 from 'd3'
import './Visualization.css'

export default function SegmentationComparison({ 
  docLen,
  trueBoundaries = [],
  predBoundaries = [],
  metricScore = null,
  tolerance = 2,
  title = "Segmentation Comparison"
}) {
  const svgRef = useRef(null)
  const containerRef = useRef(null)

  useEffect(() => {
    if (docLen <= 0) return

    const container = containerRef.current
    const svg = d3.select(svgRef.current)
    svg.selectAll("*").remove()

    const margin = { top: 80, right: 40, bottom: 60, left: 40 }
    const width = Math.max(600, container.clientWidth - margin.left - margin.right)
    const height = 150

    const g = svg
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`)

    // Scales
    const xScale = d3.scaleLinear()
      .domain([-0.5, docLen - 0.5])
      .range([0, width])

    // Identify near misses
    const trueSet = new Set(trueBoundaries)
    const nearMissSet = new Set()
    
    predBoundaries.forEach(predB => {
      if (!trueSet.has(predB)) {
        for (const trueB of trueBoundaries) {
          if (Math.abs(predB - trueB) < tolerance) {
            nearMissSet.add(predB)
            break
          }
        }
      }
    })

    // Draw ground truth boundaries
    trueBoundaries.forEach((b, idx) => {
      if (b >= 0 && b < docLen) {
        g.append("line")
          .attr("x1", xScale(b))
          .attr("x2", xScale(b))
          .attr("y1", height / 2)
          .attr("y2", height)
          .attr("stroke", "green")
          .attr("stroke-width", 3)
          .attr("opacity", 0.8)
          .attr("class", idx === 0 ? "gt-boundary" : null)
      }
    })

    // Draw prediction boundaries with color coding
    predBoundaries.forEach((b, idx) => {
      if (b >= 0 && b < docLen) {
        let color = 'red'
        if (trueSet.has(b)) {
          color = 'green' // Exact match
        } else if (nearMissSet.has(b)) {
          color = 'orange' // Near miss
        }

        g.append("line")
          .attr("x1", xScale(b))
          .attr("x2", xScale(b))
          .attr("y1", 0)
          .attr("y2", height / 2)
          .attr("stroke", color)
          .attr("stroke-width", 3)
          .attr("opacity", 0.8)
          .attr("class", idx === 0 ? "pred-boundary" : null)
      }
    })

    // Draw separator line
    g.append("line")
      .attr("x1", 0)
      .attr("x2", width)
      .attr("y1", height / 2)
      .attr("y2", height / 2)
      .attr("stroke", "#ccc")
      .attr("stroke-width", 1)

    // Add grid
    const xAxis = d3.axisBottom(xScale)
      .ticks(Math.min(20, docLen))
      .tickFormat(d3.format("d"))

    g.append("g")
      .attr("class", "x-axis")
      .attr("transform", `translate(0,${height})`)
      .call(xAxis)

    g.append("g")
      .attr("class", "grid")
      .attr("transform", `translate(0,${height})`)
      .call(xAxis.tickSize(-height).tickFormat(""))
      .attr("stroke-dasharray", "2,2")
      .attr("opacity", 0.3)

    // Add labels
    g.append("text")
      .attr("x", width / 2)
      .attr("y", height + 40)
      .attr("text-anchor", "middle")
      .attr("font-size", "12px")
      .attr("fill", "#666")
      .text("Sentence Index")

    g.append("text")
      .attr("x", 10)
      .attr("y", height / 4)
      .attr("font-size", "12px")
      .attr("fill", "#333")
      .attr("font-weight", "bold")
      .text("Prediction")

    g.append("text")
      .attr("x", 10)
      .attr("y", height * 3 / 4)
      .attr("font-size", "12px")
      .attr("fill", "#333")
      .attr("font-weight", "bold")
      .text("Ground Truth")

    // Add title
    let plotTitle = title
    if (metricScore !== null && metricScore !== undefined) {
      plotTitle += ` (Boundary Score: ${metricScore.toFixed(4)})`
    }
    svg.append("text")
      .attr("x", (width + margin.left + margin.right) / 2)
      .attr("y", 30)
      .attr("text-anchor", "middle")
      .attr("font-size", "16px")
      .attr("font-weight", "bold")
      .attr("fill", "#333")
      .text(plotTitle)

    // Add legend
    const legend = g.append("g")
      .attr("transform", `translate(${width - 180}, 20)`)

    const legendItems = [
      { color: "green", label: "Match" },
      { color: "orange", label: "Near Miss" },
      { color: "red", label: "False Positive" },
    ]

    legendItems.forEach((item, idx) => {
      legend.append("rect")
        .attr("x", 0)
        .attr("y", idx * 20)
        .attr("width", 15)
        .attr("height", 3)
        .attr("fill", item.color)
        .attr("opacity", 0.8)
      
      legend.append("text")
        .attr("x", 20)
        .attr("y", idx * 20 + 12)
        .attr("font-size", "11px")
        .text(item.label)
    })

  }, [docLen, trueBoundaries, predBoundaries, metricScore, tolerance, title])

  if (docLen <= 0) {
    return (
      <div className="visualization-placeholder">
        <p>No data available for comparison</p>
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
