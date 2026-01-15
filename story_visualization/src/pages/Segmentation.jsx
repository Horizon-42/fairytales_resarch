import React, { useState, useEffect } from 'react'
import './Segmentation.css'
import SimilarityMatrixHeatmap from '../components/SimilarityMatrixHeatmap'
import MagneticSignalChart from '../components/MagneticSignalChart'
import SegmentationComparison from '../components/SegmentationComparison'
import { extractGroundTruthFromAnnotation } from '../utils/textSpanUtils'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

export default function Segmentation({ story }) {
  const [text, setText] = useState('')
  const [sentences, setSentences] = useState([])
  const [loading, setLoading] = useState(false)  // Loading text from story
  const [segmenting, setSegmenting] = useState(false)  // Loading segmentation result
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  
  // Algorithm parameters
  const [algorithm, setAlgorithm] = useState('magnetic')
  const [windowSize, setWindowSize] = useState(3)
  const [filterWidth, setFilterWidth] = useState(2.0)
  const [threshold, setThreshold] = useState(0.7)
  const [minSegSize, setMinSegSize] = useState(3)
  const [contextWindow, setContextWindow] = useState(2)
  
  // Ground truth boundaries
  const [referenceBoundaries, setReferenceBoundaries] = useState([])
  const [referenceInput, setReferenceInput] = useState('')
  
  // Ground truth segments from annotation
  const [gtSegments, setGtSegments] = useState([])

  // Extract ground truth from annotation when text and sentences are ready
  useEffect(() => {
    if (text && sentences.length > 0 && story?.annotation) {
      try {
        const gtData = extractGroundTruthFromAnnotation(story.annotation, text, sentences)
        setGtSegments(gtData.segments)
        setReferenceBoundaries(gtData.boundaries)
        if (gtData.boundaries.length > 0) {
          setReferenceInput(gtData.boundaries.join(', '))
        }
        console.log(`Extracted ${gtData.boundaries.length} ground truth boundaries from annotation`)
      } catch (err) {
        console.error('Failed to extract ground truth from annotation:', err)
      }
    } else {
      setGtSegments([])
    }
  }, [text, sentences, story?.annotation])

  useEffect(() => {
    if (story) {
      loadStoryText(story)
    } else {
      // Clear text if no story selected
      setText('')
      setSentences([])
      setResult(null)
      setGtSegments([])
    }
  }, [story])

  const loadStoryText = async (storyData) => {
    try {
      setLoading(true)
      setError(null)
      let loadedText = ''

      // Method 1: Get text from story object directly (from file)
      // story.text is already loaded from file in App.jsx
      if (storyData.text && storyData.text.trim()) {
        loadedText = storyData.text
        console.log('Loaded text from story file')
      }

      if (loadedText && loadedText.trim()) {
        setText(loadedText)
        splitSentences(loadedText)
        setError(null)
      } else {
        const errorMsg = `Could not load story text for "${storyData.name || storyData.id}". The story file may be empty.`
        setError(errorMsg)
        setText('')
        setSentences([])
      }
    } catch (err) {
      console.error('Failed to load story text:', err)
      setError(`Failed to load story text: ${err.message}`)
      setText('')
      setSentences([])
    } finally {
      setLoading(false)
    }
  }

  const splitSentences = (text) => {
    // Simple sentence splitting
    const sentences = text
      .split(/[。！？.!\?]+/)
      .map(s => s.trim())
      .filter(s => s.length > 0)
    setSentences(sentences)
  }

  const handleTextChange = (e) => {
    const newText = e.target.value
    setText(newText)
    splitSentences(newText)
  }

  const handleReferenceInputChange = (e) => {
    const input = e.target.value
    setReferenceInput(input)
    // Parse comma-separated numbers
    const boundaries = input
      .split(',')
      .map(s => parseInt(s.trim()))
      .filter(n => !isNaN(n))
    setReferenceBoundaries(boundaries)
  }

  const handleSegment = async () => {
    if (!text.trim()) {
      setError('Please provide text to segment')
      return
    }

    setSegmenting(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch(`${BACKEND_URL}/api/text/segment`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: text,
          sentences: sentences.length > 0 ? sentences : null,
          algorithm: algorithm,
          context_window: contextWindow,
          window_size: windowSize,
          filter_width: filterWidth,
          threshold: threshold,
          min_seg_size: minSegSize,
          reference_boundaries: referenceBoundaries.length > 0 ? referenceBoundaries : null,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Segmentation failed')
      }

      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError(err.message || 'Failed to segment text')
      console.error('Segmentation error:', err)
    } finally {
      setSegmenting(false)
    }
  }

  const getSegmentColor = (index) => {
    const colors = [
      '#e3f2fd', '#f3e5f5', '#e8f5e9', '#fff3e0',
      '#fce4ec', '#e0f2f1', '#f1f8e9', '#fff8e1',
      '#ede7f6', '#e8eaf6', '#f9fbe7', '#fffde7',
    ]
    return colors[index % colors.length]
  }

  // Render text with ground truth segment highlighting
  const renderTextWithSegments = () => {
    if (!text || gtSegments.length === 0) {
      return text
    }

    // Create segments sorted by character position
    const sortedSegments = [...gtSegments].sort((a, b) => a.startChar - b.startChar)
    
    // Build rendering parts
    const parts = []
    let currentPos = 0
    
    sortedSegments.forEach((segment, idx) => {
      // Text before this segment
      if (segment.startChar > currentPos) {
        parts.push({
          text: text.substring(currentPos, segment.startChar),
          type: 'normal',
          segmentId: null
        })
      }
      
      // This segment
      parts.push({
        text: text.substring(segment.startChar, segment.endChar),
        type: 'gt-segment',
        segmentId: segment.segmentId,
        segment: segment
      })
      
      currentPos = segment.endChar
    })
    
    // Remaining text
    if (currentPos < text.length) {
      parts.push({
        text: text.substring(currentPos),
        type: 'normal',
        segmentId: null
      })
    }
    
    return parts.map((part, idx) => {
      if (part.type === 'gt-segment') {
        const bgColor = getSegmentColor(part.segmentId - 1)
        return (
          <span
            key={idx}
            className="gt-text-segment"
            style={{ backgroundColor: bgColor }}
            title={`Segment ${part.segmentId}: ${part.segment.description || part.segment.eventType}`}
          >
            {part.text}
          </span>
        )
      }
      return <span key={idx}>{part.text}</span>
    })
  }

  return (
    <div className="segmentation-page">
      <div className="segmentation-header">
        <h2>Text Segmentation</h2>
        <p>
          Automatically segment story text into semantic segments using LLM embeddings
          {story && (
            <span className="current-story">
              {' '}• Current Story: <strong>{story.name || story.id}</strong>
            </span>
          )}
        </p>
      </div>

      {!story && (
        <div className="no-story-message">
          <p>Please select a story from the dropdown above to begin segmentation.</p>
        </div>
      )}

      {story && (
        <div className="segmentation-content">
          {/* Story Info Section */}
          <div className="story-info-section">
            <div className="story-info">
              <label>Current Story:</label>
              <span>{story.name || story.id}</span>
            </div>
            {loading && (
              <div className="loading-indicator">
                <span>Loading story text...</span>
              </div>
            )}
            {segmenting && (
              <div className="loading-indicator">
                <span>Segmenting text...</span>
              </div>
            )}
            {text && (
              <div className="text-info">
                {sentences.length} sentences loaded
              </div>
            )}
          </div>

          {/* Input Section (Read-only display) */}
          <div className="input-section">
            <div className="input-group">
              <label htmlFor="text-input">Story Text:</label>
              {gtSegments.length > 0 ? (
                <div className="text-display-with-segments">
                  <div className="gt-segments-legend">
                    <strong>Ground Truth Segments (from annotation):</strong>
                    {gtSegments.map((seg) => (
                      <span 
                        key={seg.segmentId} 
                        className="legend-item"
                        style={{ backgroundColor: getSegmentColor(seg.segmentId - 1) }}
                      >
                        Seg {seg.segmentId} (Sentences {seg.startSentenceIdx}-{seg.endSentenceIdx})
                      </span>
                    ))}
                  </div>
                  <div className="text-with-highlights" id="story-text-display">
                    {renderTextWithSegments()}
                  </div>
                  <div className="text-info">
                    {sentences.length} sentences detected • {gtSegments.length} ground truth segments loaded from annotation
                  </div>
                </div>
              ) : (
                <>
                  <textarea
                    id="text-input"
                    value={text}
                    onChange={handleTextChange}
                    placeholder={loading ? "Loading story text..." : story ? "Select a story to load text..." : "Please select a story from the dropdown above"}
                    rows={12}
                    readOnly={false}
                  />
                  <div className="text-info">
                    {sentences.length} sentences detected
                    {story?.annotation && (
                      <span className="annotation-hint"> • Annotation loaded but no narrative events found</span>
                    )}
                    {text && !story?.annotation && (
                      <span className="text-edit-hint">(Text can be edited if needed)</span>
                    )}
                  </div>
                </>
              )}
            </div>

          {/* Algorithm Parameters */}
          <div className="parameters-section">
            <h3>Algorithm Parameters</h3>
            <div className="params-grid">
              <div className="param-group">
                <label>Algorithm:</label>
                <select value={algorithm} onChange={(e) => setAlgorithm(e.target.value)}>
                  <option value="magnetic">Magnetic Clustering</option>
                  <option value="graph">GraphSegSM</option>
                </select>
              </div>

              <div className="param-group">
                <label>Context Window:</label>
                <input
                  type="number"
                  min="1"
                  max="5"
                  value={contextWindow}
                  onChange={(e) => setContextWindow(parseInt(e.target.value))}
                />
              </div>

              {algorithm === 'magnetic' && (
                <>
                  <div className="param-group">
                    <label>Window Size:</label>
                    <input
                      type="number"
                      min="1"
                      max="10"
                      value={windowSize}
                      onChange={(e) => setWindowSize(parseInt(e.target.value))}
                    />
                  </div>
                  <div className="param-group">
                    <label>Filter Width:</label>
                    <input
                      type="number"
                      step="0.1"
                      min="0.1"
                      max="10"
                      value={filterWidth}
                      onChange={(e) => setFilterWidth(parseFloat(e.target.value))}
                    />
                  </div>
                </>
              )}

              {algorithm === 'graph' && (
                <>
                  <div className="param-group">
                    <label>Threshold:</label>
                    <input
                      type="number"
                      step="0.05"
                      min="0"
                      max="1"
                      value={threshold}
                      onChange={(e) => setThreshold(parseFloat(e.target.value))}
                    />
                  </div>
                  <div className="param-group">
                    <label>Min Segment Size:</label>
                    <input
                      type="number"
                      min="1"
                      max="20"
                      value={minSegSize}
                      onChange={(e) => setMinSegSize(parseInt(e.target.value))}
                    />
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Ground Truth Section */}
          <div className="ground-truth-section">
            <h3>Ground Truth</h3>
            {gtSegments.length > 0 ? (
              <div className="gt-info">
                <div className="gt-summary">
                  <strong>Loaded from annotation:</strong> {gtSegments.length} segments, {referenceBoundaries.length} boundaries
                  <br />
                  <small>Segments are highlighted in the text above. Boundaries: {referenceBoundaries.join(', ') || 'None'}</small>
                </div>
              </div>
            ) : (
              <div className="param-group">
                <label>Reference Boundaries (comma-separated, optional):</label>
                <input
                  type="text"
                  value={referenceInput}
                  onChange={handleReferenceInputChange}
                  placeholder="e.g., 2, 5, 8"
                />
                <small>Boundary indices: each index i means a boundary between sentence i and i+1. 
                  {story?.annotation ? ' (No narrative events found in annotation)' : ' (No annotation loaded)'}
                </small>
              </div>
            )}
          </div>

          {error && !loading && (
            <div className="error-message">
              <strong>Error:</strong> {error}
            </div>
          )}

          <button
            className="segment-button"
            onClick={handleSegment}
            disabled={loading || segmenting || !text.trim()}
          >
            {segmenting ? 'Segmenting...' : loading ? 'Loading story...' : 'Segment Text'}
          </button>
        </div>

        {/* Results Section */}
        {result && (
          <div className="results-section">
            <div className="results-header">
              <h3>Segmentation Results</h3>
              {result.meta.evaluation_score !== null && (
                <div className="evaluation-score">
                  <strong>Boundary Score:</strong> {result.meta.evaluation_score.toFixed(4)}
                </div>
              )}
              <div className="results-meta">
                <span>Algorithm: {result.meta.algorithm}</span>
                <span>Segments: {result.segments.length}</span>
                <span>Boundaries: {result.boundaries.join(', ') || 'None'}</span>
              </div>
            </div>

            {/* Segments Display */}
            <div className="segments-container">
              {result.segments.map((segment, idx) => (
                <div
                  key={segment.segment_id}
                  className="segment-card"
                  style={{ backgroundColor: getSegmentColor(idx) }}
                >
                  <div className="segment-header">
                    <h4>
                      Segment {segment.segment_id} 
                      <span className="segment-range">
                        (Sentences {segment.start_sentence_idx} - {segment.end_sentence_idx})
                      </span>
                    </h4>
                  </div>
                  <div className="segment-text">
                    {segment.text}
                  </div>
                </div>
              ))}
            </div>

            {/* Boundary Comparison */}
            {referenceBoundaries.length > 0 && result.meta.evaluation_score !== null && (
              <div className="comparison-section">
                <h4>Boundary Comparison</h4>
                <div className="comparison-grid">
                  <div className="comparison-item">
                    <strong>Reference Boundaries:</strong>
                    <span>{referenceBoundaries.join(', ')}</span>
                  </div>
                  <div className="comparison-item">
                    <strong>Predicted Boundaries:</strong>
                    <span>{result.boundaries.join(', ') || 'None'}</span>
                  </div>
                  <div className="comparison-item">
                    <strong>Score:</strong>
                    <span className="score-value">{result.meta.evaluation_score.toFixed(4)}</span>
                  </div>
                </div>
              </div>
            )}

            {/* Visualization Section */}
            {result.visualization && (
              <div className="visualization-section">
                <h3>Visualization</h3>
                
                {/* Similarity Matrix Heatmap */}
                {result.visualization.similarity_matrix && (
                  <div className="viz-item">
                    <h4>Similarity Matrix</h4>
                    <SimilarityMatrixHeatmap
                      similarityMatrix={result.visualization.similarity_matrix}
                      groundTruthBoundaries={referenceBoundaries}
                      title="Cosine Similarity Matrix"
                    />
                  </div>
                )}

                {/* Magnetic Signal Chart (for Magnetic Clustering) */}
                {result.meta.algorithm === 'magnetic' && 
                 result.visualization.raw_forces && (
                  <div className="viz-item">
                    <h4>Magnetic Signal Analysis</h4>
                    <MagneticSignalChart
                      rawForces={result.visualization.raw_forces}
                      smoothedForces={result.visualization.smoothed_forces}
                      predictedBoundaries={result.boundaries}
                      title="Magnetic Clustering Signal Analysis"
                    />
                  </div>
                )}

                {/* Segmentation Comparison */}
                {referenceBoundaries.length > 0 && result.segments.length > 0 && (
                  <div className="viz-item">
                    <h4>Segmentation Comparison</h4>
                    <SegmentationComparison
                      docLen={result.segments[result.segments.length - 1].end_sentence_idx + 1}
                      trueBoundaries={referenceBoundaries}
                      predBoundaries={result.boundaries}
                      metricScore={result.meta.evaluation_score}
                      title="Segmentation Comparison"
                    />
                  </div>
                )}
              </div>
            )}
          </div>
        )}
        </div>
      )}
    </div>
  )
}
