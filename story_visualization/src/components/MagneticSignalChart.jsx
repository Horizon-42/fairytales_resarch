import React, { useEffect, useRef } from 'react'
import * as d3 from 'd3'
import './Visualization.css'

export default function MagneticSignalChart({ 
  rawForces,
  smoothedForces = null,
  predictedBoundaries = [],
  title = "Magnetic Clustering Signal Analysis"
}) {
  const svgRef = useRef(null)
  const containerRef = useRef(null)

  useEffect(() => {
    if (!rawForces || !rawForces.length) return

    const container = containerRef.current
    const svg = d3.select(svgRef.current)
    svg.selectAll("*").remove()

    const margin = { top: 60, right: 80, bottom: 60, left: 80 }
    const width = container.clientWidth - margin.left - margin.right
    const height = 300

    const g = svg
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`)

    // Prepare data
    const data = rawForces.map((val, i) => ({ x: i, raw: val, smoothed: smoothedForces ? smoothedForces[i] : val }))
    const targetSignal = smoothedForces || rawForces

    // Scales
    const xScale = d3.scaleLinear()
      .domain([0, rawForces.length - 1])
      .range([0, width])

    const yExtent = d3.extent([...rawForces, ...(smoothedForces || [])])
    const yScale = d3.scaleLinear()
      .domain([yExtent[0] * 1.1, yExtent[1] * 1.1])
      .range([height, 0])

    // Draw zero line
    const zeroY = yScale(0)
    g.append("line")
      .attr("x1", 0)
      .attr("x2", width)
      .attr("y1", zeroY)
      .attr("y2", zeroY)
      .attr("stroke", "#000")
      .attr("stroke-width", 1)
      .attr("opacity", 0.5)

    // Fill areas above and below zero
    const areaPositive = d3.area()
      .x(d => xScale(d.x))
      .y0(zeroY)
      .y1(d => yScale(Math.max(0, d.smoothed)))
      .curve(d3.curveMonotoneX)

    const areaNegative = d3.area()
      .x(d => xScale(d.x))
      .y0(zeroY)
      .y1(d => yScale(Math.min(0, d.smoothed)))
      .curve(d3.curveMonotoneX)

    g.append("path")
      .datum(data)
      .attr("fill", "blue")
      .attr("opacity", 0.1)
      .attr("d", areaPositive)

    g.append("path")
      .datum(data)
      .attr("fill", "red")
      .attr("opacity", 0.1)
      .attr("d", areaNegative)

    // Draw raw signal
    const rawLine = d3.line()
      .x(d => xScale(d.x))
      .y(d => yScale(d.raw))
      .curve(d3.curveMonotoneX)

    g.append("path")
      .datum(data)
      .attr("fill", "none")
      .attr("stroke", "lightgray")
      .attr("stroke-width", 1)
      .attr("opacity", 0.5)
      .attr("d", rawLine)
      .attr("class", "raw-signal")

    // Draw smoothed signal if available
    if (smoothedForces) {
      const smoothedLine = d3.line()
        .x(d => xScale(d.x))
        .y(d => yScale(d.smoothed))
        .curve(d3.curveMonotoneX)

      g.append("path")
        .datum(data)
        .attr("fill", "none")
        .attr("stroke", "purple")
        .attr("stroke-width", 2)
        .attr("d", smoothedLine)
        .attr("class", "smoothed-signal")
    }

    // Draw predicted boundaries
    predictedBoundaries.forEach((boundary, idx) => {
      if (boundary >= 0 && boundary < rawForces.length) {
        g.append("line")
          .attr("x1", xScale(boundary))
          .attr("x2", xScale(boundary))
          .attr("y1", 0)
          .attr("y2", height)
          .attr("stroke", "red")
          .attr("stroke-width", 2)
          .attr("stroke-dasharray", "4,4")
          .attr("opacity", 0.7)
          .attr("class", idx === 0 ? "predicted-boundary" : null)
      }
    })

    // Add axes
    const xAxis = d3.axisBottom(xScale)
      .ticks(10)
      .tickFormat(d3.format("d"))

    const yAxis = d3.axisLeft(yScale)
      .ticks(8)

    g.append("g")
      .attr("class", "x-axis")
      .attr("transform", `translate(0,${height})`)
      .call(xAxis)

    g.append("g")
      .attr("class", "y-axis")
      .call(yAxis)

    // Add grid
    g.append("g")
      .attr("class", "grid")
      .attr("transform", `translate(0,${height})`)
      .call(xAxis.tickSize(-height).tickFormat(""))

    g.append("g")
      .attr("class", "grid")
      .call(yAxis.tickSize(-width).tickFormat(""))

    // Add labels
    g.append("text")
      .attr("x", width / 2)
      .attr("y", height + 50)
      .attr("text-anchor", "middle")
      .attr("font-size", "12px")
      .attr("fill", "#666")
      .text("Sentence Gap Index")

    g.append("text")
      .attr("transform", "rotate(-90)")
      .attr("x", -height / 2)
      .attr("y", -50)
      .attr("text-anchor", "middle")
      .attr("font-size", "12px")
      .attr("fill", "#666")
      .text("Magnetization Strength (b_i)")

    // Add title
    svg.append("text")
      .attr("x", (width + margin.left + margin.right) / 2)
      .attr("y", 30)
      .attr("text-anchor", "middle")
      .attr("font-size", "16px")
      .attr("font-weight", "bold")
      .attr("fill", "#333")
      .text(title)

    // Add legend
    const legend = g.append("g")
      .attr("transform", `translate(${width - 150}, 20)`)

    if (smoothedForces) {
      legend.append("line")
        .attr("x1", 0)
        .attr("x2", 20)
        .attr("y1", 0)
        .attr("y2", 0)
        .attr("stroke", "lightgray")
        .attr("stroke-width", 1)
        .attr("opacity", 0.5)
      
      legend.append("text")
        .attr("x", 25)
        .attr("y", 5)
        .attr("font-size", "11px")
        .text("Raw Magnetization")

      legend.append("line")
        .attr("x1", 0)
        .attr("x2", 20)
        .attr("y1", 20)
        .attr("y2", 20)
        .attr("stroke", "purple")
        .attr("stroke-width", 2)
      
      legend.append("text")
        .attr("x", 25)
        .attr("y", 25)
        .attr("font-size", "11px")
        .text("Smoothed Signal")
    }

    if (predictedBoundaries.length > 0) {
      legend.append("line")
        .attr("x1", 0)
        .attr("x2", 20)
        .attr("y1", 40)
        .attr("y2", 40)
        .attr("stroke", "red")
        .attr("stroke-width", 2)
        .attr("stroke-dasharray", "4,4")
        .attr("opacity", 0.7)
      
      legend.append("text")
        .attr("x", 25)
        .attr("y", 45)
        .attr("font-size", "11px")
        .text("Predicted Boundary")
    }

  }, [rawForces, smoothedForces, predictedBoundaries, title])

  if (!rawForces || !rawForces.length) {
    return (
      <div className="visualization-placeholder">
        <p>No magnetic signal data available</p>
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
