import React, { useState, useEffect } from 'react'
import './Segmentation.css'
import SimilarityMatrixHeatmap from '../components/SimilarityMatrixHeatmap'
import MagneticSignalChart from '../components/MagneticSignalChart'
import GraphSegSMChart from '../components/GraphSegSMChart'
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
  
  // Display mode: 'gt', 'predicted', or 'both'
  const [displayMode, setDisplayMode] = useState('predicted')
  
  // Update display mode when result or gtSegments change
  useEffect(() => {
    if (result && result.segments && result.segments.length > 0) {
      // If user switched to 'gt' or 'both' but no GT segments, switch to 'predicted'
      if (gtSegments.length === 0 && (displayMode === 'both' || displayMode === 'gt')) {
        setDisplayMode('predicted')
      }
    }
  }, [result, gtSegments.length, displayMode])

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

  // Build predicted segments from result
  const buildPredictedSegments = () => {
    if (!result || !result.segments || result.segments.length === 0) {
      return []
    }

    // Split text into sentences to find character positions
    const sentenceMatches = []
    let lastIndex = 0
    const sentenceRegex = /[^。！？.!\?]+[。！？.!\?]+/g
    let match
    
    while ((match = sentenceRegex.exec(text)) !== null) {
      sentenceMatches.push({
        start: match.index,
        end: match.index + match[0].length
      })
      lastIndex = match.index + match[0].length
    }
    
    if (lastIndex < text.length) {
      sentenceMatches.push({
        start: lastIndex,
        end: text.length
      })
    }

    // Build predicted segments
    const predictedSegments = []
    result.segments.forEach((segment, idx) => {
      const startSentenceIdx = segment.start_sentence_idx
      const endSentenceIdx = segment.end_sentence_idx
      
      // Try to find text positions using segment.text if available
      if (segment.text && segment.text.trim()) {
        const segmentText = segment.text.trim()
        const charIndex = text.indexOf(segmentText)
        
        if (charIndex !== -1) {
          predictedSegments.push({
            segmentId: segment.segment_id,
            startChar: charIndex,
            endChar: charIndex + segmentText.length
          })
          return
        }
      }
      
      // Fallback: use sentence indices
      if (startSentenceIdx >= 0 && startSentenceIdx < sentenceMatches.length &&
          endSentenceIdx >= 0 && endSentenceIdx < sentenceMatches.length) {
        const startChar = sentenceMatches[startSentenceIdx].start
        const endChar = sentenceMatches[endSentenceIdx].end
        
        predictedSegments.push({
          segmentId: segment.segment_id,
          startChar: startChar,
          endChar: endChar
        })
      }
    })

    return predictedSegments
  }

  // Render text with both ground truth and predicted segments for comparison (split view)
  const renderTextWithComparison = () => {
    if (!text) {
      return <div className="text-with-highlights">{text}</div>
    }

    const predictedSegments = buildPredictedSegments()
    
    if (predictedSegments.length === 0 && gtSegments.length === 0) {
      return <div className="text-with-highlights">{text}</div>
    }

    // Render predicted segments (upper half)
    const predictedParts = []
    let predCurrentPos = 0
    
    predictedSegments.forEach((segment) => {
      if (segment.startChar > predCurrentPos) {
        predictedParts.push({
          text: text.substring(predCurrentPos, segment.startChar),
          type: 'normal'
        })
      }
      predictedParts.push({
        text: text.substring(segment.startChar, segment.endChar),
        type: 'predicted',
        segmentId: segment.segmentId
      })
      predCurrentPos = segment.endChar
    })
    
    if (predCurrentPos < text.length) {
      predictedParts.push({
        text: text.substring(predCurrentPos),
        type: 'normal'
      })
    }

    // Render ground truth segments (lower half)
    const gtParts = []
    let gtCurrentPos = 0
    const sortedGtSegments = [...gtSegments].sort((a, b) => a.startChar - b.startChar)
    
    sortedGtSegments.forEach((segment) => {
      if (segment.startChar > gtCurrentPos) {
        gtParts.push({
          text: text.substring(gtCurrentPos, segment.startChar),
          type: 'normal'
        })
      }
      gtParts.push({
        text: text.substring(segment.startChar, segment.endChar),
        type: 'ground-truth',
        segmentId: segment.segmentId
      })
      gtCurrentPos = segment.endChar
    })
    
    if (gtCurrentPos < text.length) {
      gtParts.push({
        text: text.substring(gtCurrentPos),
        type: 'normal'
      })
    }

    // Render both layers: predicted on top (upper half), GT on bottom (lower half)
    return (
      <div className="comparison-text-container">
        {/* Upper half: Predicted segments */}
        <div className="comparison-text-upper">
          {predictedParts.map((part, idx) => {
            if (part.type === 'predicted') {
              return (
                <span
                  key={idx}
                  className="predicted-text-segment-bg"
                  style={{ backgroundColor: '#fee2e2' }}
                  title={`Predicted Segment ${part.segmentId}`}
                >
                  {part.text}
                </span>
              )
            }
            return <span key={idx}>{part.text}</span>
          })}
        </div>
        {/* Lower half: Ground truth segments */}
        <div className="comparison-text-lower">
          {gtParts.map((part, idx) => {
            if (part.type === 'ground-truth') {
              const bgColor = getSegmentColor(part.segmentId - 1)
              return (
                <span
                  key={idx}
                  className="gt-text-segment"
                  style={{ backgroundColor: bgColor }}
                  title={`Ground Truth Segment ${part.segmentId}`}
                >
                  {part.text}
                </span>
              )
            }
            return <span key={idx}>{part.text}</span>
          })}
        </div>
      </div>
    )
  }

  // Render text with predicted segments only (background color approach)
  const renderTextWithPredictedBoundaries = () => {
    if (!text || !result || !result.segments || result.segments.length === 0) {
      return <div className="text-with-highlights">{text}</div>
    }

    // Split text into sentences to find character positions
    const sentenceMatches = []
    let lastIndex = 0
    const sentenceRegex = /[^。！？.!\?]+[。！？.!\?]+/g
    let match
    
    while ((match = sentenceRegex.exec(text)) !== null) {
      sentenceMatches.push({
        start: match.index,
        end: match.index + match[0].length
      })
      lastIndex = match.index + match[0].length
    }
    
    if (lastIndex < text.length) {
      sentenceMatches.push({
        start: lastIndex,
        end: text.length
      })
    }

    if (sentenceMatches.length === 0) {
      return <div className="text-with-highlights">{text}</div>
    }

    const predictedSegments = buildPredictedSegments()

    if (predictedSegments.length === 0) {
      return <div className="text-with-highlights">{text}</div>
    }

    // Sort by position
    predictedSegments.sort((a, b) => a.startChar - b.startChar)

    // Build rendering parts
    const parts = []
    let currentPos = 0
    
    predictedSegments.forEach((segment) => {
      // Text before this segment
      if (segment.startChar > currentPos) {
        parts.push({
          text: text.substring(currentPos, segment.startChar),
          type: 'normal'
        })
      }
      
      // This segment
      parts.push({
        text: text.substring(segment.startChar, segment.endChar),
        type: 'predicted',
        segmentId: segment.segmentId
      })
      
      currentPos = segment.endChar
    })
    
    // Remaining text
    if (currentPos < text.length) {
      parts.push({
        text: text.substring(currentPos),
        type: 'normal'
      })
    }


    return (
      <>
        {parts.map((part, idx) => {
          if (part.type === 'predicted') {
            return (
              <span
                key={idx}
                className="predicted-text-segment-bg"
                style={{ backgroundColor: '#fee2e2' }}
                title={`Predicted Segment ${part.segmentId}`}
              >
                {part.text}
              </span>
            )
          }
          return <span key={idx}>{part.text}</span>
        })}
      </>
    )
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
              {(gtSegments.length > 0 && !result) || (result && result.segments && result.segments.length > 0) ? (
                <div className="text-display-with-segments">
                  <div className="gt-segments-legend">
                    {/* Display Mode Toggle - show when there's a result or both GT and result */}
                    {result && result.segments && result.segments.length > 0 && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap', marginBottom: '0.5rem' }}>
                        <strong>Display Mode:</strong>
                        <div className="display-mode-toggle">
                          <button
                            className={`mode-button ${displayMode === 'gt' ? 'active' : ''}`}
                            onClick={() => setDisplayMode('gt')}
                            disabled={gtSegments.length === 0}
                            title="Show Ground Truth only"
                          >
                            Ground Truth
                          </button>
                          <button
                            className={`mode-button ${displayMode === 'predicted' ? 'active' : ''}`}
                            onClick={() => setDisplayMode('predicted')}
                            title="Show Predicted only"
                          >
                            Predicted
                          </button>
                          <button
                            className={`mode-button ${displayMode === 'both' ? 'active' : ''}`}
                            onClick={() => setDisplayMode('both')}
                            disabled={gtSegments.length === 0}
                            title="Show both Ground Truth and Predicted"
                          >
                            Both
                          </button>
                        </div>
                      </div>
                    )}
                    
                    {/* Show GT legend when displaying GT or both */}
                    {(displayMode === 'gt' || displayMode === 'both' || !result) && gtSegments.length > 0 && (
                      <>
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
                      </>
                    )}
                    
                    {/* Show Predicted legend when displaying predicted or both */}
                    {result && result.segments && result.segments.length > 0 && (displayMode === 'predicted' || displayMode === 'both') && (
                      <>
                        <strong style={{ marginTop: '0.5rem', display: 'block' }}>Predicted Segmentation:</strong>
                        {result.boundaries && result.boundaries.length > 0 && (
                          <span className="legend-item" style={{ backgroundColor: '#fee2e2', border: '1px dashed #ef4444' }}>
                            Boundaries: {result.boundaries.join(', ')}
                          </span>
                        )}
                        <span className="legend-item" style={{ backgroundColor: '#fee2e2', border: '1px dashed #ef4444' }}>
                          {result.segments.length} predicted segments
                        </span>
                      </>
                    )}
                  </div>
                  <div className="text-with-highlights" id="story-text-display">
                    {result && result.segments && result.segments.length > 0
                      ? (displayMode === 'gt' ? renderTextWithSegments() : 
                         displayMode === 'both' ? renderTextWithComparison() : 
                         renderTextWithPredictedBoundaries())
                      : renderTextWithSegments()}
                  </div>
                  <div className="text-info">
                    {sentences.length} sentences detected
                    {result && result.segments && result.segments.length > 0 && (displayMode === 'predicted' || displayMode === 'both') ? ` • ${result.segments.length} predicted segments` : ''}
                    {(displayMode === 'gt' || displayMode === 'both' || !result) && gtSegments.length > 0 ? ` • ${gtSegments.length} ground truth segments` : ''}
                  </div>
                </div>
              ) : (
                <>
                  {result && result.segments && result.segments.length > 0 ? (
                    <div className="text-display-with-segments">
                      <div className="gt-segments-legend">
                        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
                          <strong>Display Mode:</strong>
                          <div className="display-mode-toggle">
                            <button
                              className={`mode-button ${displayMode === 'gt' ? 'active' : ''}`}
                              onClick={() => setDisplayMode('gt')}
                              disabled={gtSegments.length === 0}
                              title="Show Ground Truth only"
                            >
                              Ground Truth
                            </button>
                            <button
                              className={`mode-button ${displayMode === 'predicted' ? 'active' : ''}`}
                              onClick={() => setDisplayMode('predicted')}
                              title="Show Predicted only"
                            >
                              Predicted
                            </button>
                            <button
                              className={`mode-button ${displayMode === 'both' ? 'active' : ''}`}
                              onClick={() => setDisplayMode('both')}
                              disabled={gtSegments.length === 0}
                              title="Show both Ground Truth and Predicted"
                            >
                              Both
                            </button>
                          </div>
                        </div>
                        {displayMode === 'gt' || displayMode === 'both' ? (
                          <>
                            <strong style={{ marginTop: '0.5rem', display: 'block' }}>Ground Truth:</strong>
                            {gtSegments.map((seg) => (
                              <span 
                                key={seg.segmentId} 
                                className="legend-item"
                                style={{ backgroundColor: getSegmentColor(seg.segmentId - 1) }}
                              >
                                Seg {seg.segmentId}
                              </span>
                            ))}
                          </>
                        ) : null}
                        {displayMode === 'predicted' || displayMode === 'both' ? (
                          <>
                            <strong style={{ marginTop: '0.5rem', display: 'block' }}>Predicted:</strong>
                            {result.boundaries && result.boundaries.length > 0 && (
                              <span className="legend-item" style={{ backgroundColor: '#fee2e2', border: '1px dashed #ef4444' }}>
                                Boundaries: {result.boundaries.join(', ')}
                              </span>
                            )}
                            <span className="legend-item" style={{ backgroundColor: '#fee2e2', border: '1px dashed #ef4444' }}>
                              {result.segments.length} segments
                            </span>
                          </>
                        ) : null}
                      </div>
                      <div className="text-with-highlights" id="story-text-display">
                        {displayMode === 'gt' ? renderTextWithSegments() : 
                         displayMode === 'both' ? renderTextWithComparison() : 
                         renderTextWithPredictedBoundaries()}
                      </div>
                      <div className="text-info">
                        {sentences.length} sentences detected
                        {displayMode === 'predicted' || displayMode === 'both' ? ` • ${result.segments.length} predicted segments` : ''}
                        {displayMode === 'gt' || displayMode === 'both' ? ` • ${gtSegments.length} ground truth segments` : ''}
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

                {/* Graph Structure (for GraphSegSM) */}
                {result.meta.algorithm === 'graph' && 
                 result.visualization.graph && (
                  <div className="viz-item">
                    <h4>Graph Structure</h4>
                    <GraphSegSMChart
                      graph={result.visualization.graph}
                      threshold={result.visualization.threshold || 0.7}
                      cliques={result.visualization.cliques || null}
                      predictedBoundaries={result.boundaries}
                      title="GraphSegSM Structure"
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
