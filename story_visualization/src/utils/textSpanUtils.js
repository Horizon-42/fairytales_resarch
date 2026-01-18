/**
 * Utilities for converting text_span character offsets to sentence indices
 * and building ground truth boundaries from narrative events.
 */

/**
 * Convert character offsets to sentence indices.
 * @param {string} text - Full text
 * @param {number} charOffset - Character offset in the text
 * @param {Array<string>} sentences - Array of sentences
 * @returns {number} - Sentence index (0-based)
 */
export function charOffsetToSentenceIndex(text, charOffset, sentences) {
  if (!sentences || sentences.length === 0) return 0
  if (charOffset <= 0) return 0
  if (charOffset >= text.length) return Math.max(0, sentences.length - 1)
  
  // Build mapping of character positions to sentence indices
  // by splitting text on sentence delimiters (same as splitSentences function)
  const sentencePattern = /[。！？.!\?]+/
  const parts = text.split(sentencePattern)
  let cumulativePos = 0
  const sentenceBoundaries = []
  
  for (let i = 0; i < Math.min(parts.length, sentences.length); i++) {
    const part = parts[i].trim()
    if (!part) continue
    
    const sentenceStart = cumulativePos
    // Find where this sentence starts in the original text
    const actualStart = text.indexOf(part, cumulativePos)
    const actualStartPos = actualStart !== -1 ? actualStart : cumulativePos
    const actualEndPos = actualStartPos + part.length
    
    sentenceBoundaries.push({
      start: actualStartPos,
      end: actualEndPos,
      sentenceIdx: i
    })
    
    // Move cumulative position: account for sentence + delimiter
    cumulativePos = actualEndPos
    // Find the delimiter after this sentence
    const delimiterMatch = text.substring(cumulativePos).match(/^[。！？.!\?]+/)
    if (delimiterMatch) {
      cumulativePos += delimiterMatch[0].length
    }
  }
  
  // If we couldn't build boundaries, use approximate method
  if (sentenceBoundaries.length === 0) {
    const avgSentenceLength = text.length / Math.max(1, sentences.length)
    const estimatedIdx = Math.floor(charOffset / avgSentenceLength)
    return Math.min(estimatedIdx, sentences.length - 1)
  }
  
  // Find which sentence the charOffset belongs to
  for (let i = 0; i < sentenceBoundaries.length; i++) {
    const boundary = sentenceBoundaries[i]
    if (charOffset >= boundary.start && charOffset < boundary.end) {
      return boundary.sentenceIdx
    }
    // Check if we're past the last boundary
    if (i === sentenceBoundaries.length - 1 && charOffset >= boundary.end) {
      return boundary.sentenceIdx
    }
  }
  
  // If not found exactly, find closest boundary
  let closestIdx = 0
  let minDist = Infinity
  for (const boundary of sentenceBoundaries) {
    const distToStart = Math.abs(charOffset - boundary.start)
    const distToEnd = Math.abs(charOffset - boundary.end)
    const minDistHere = Math.min(distToStart, distToEnd)
    if (minDistHere < minDist) {
      minDist = minDistHere
      closestIdx = boundary.sentenceIdx
    }
  }
  
  return Math.max(0, Math.min(closestIdx, sentences.length - 1))
}

/**
 * Extract ground truth boundaries from narrative events.
 * @param {Object} annotationData - JSON v3 annotation data
 * @param {string} fullText - Full story text
 * @param {Array<string>} sentences - Array of sentences
 * @returns {Object} - { boundaries: Array<number>, segments: Array<Object> }
 */
export function extractGroundTruthFromAnnotation(annotationData, fullText, sentences) {
  if (!annotationData || !annotationData.narrative_events) {
    return { boundaries: [], segments: [] }
  }

  const events = annotationData.narrative_events
    .filter(e => e && e.text_span && e.text_span.start !== undefined && e.text_span.end !== undefined)
    .sort((a, b) => {
      // Sort by time_order if available, otherwise by text_span.start
      if (a.time_order !== undefined && b.time_order !== undefined) {
        return a.time_order - b.time_order
      }
      return (a.text_span?.start || 0) - (b.text_span?.start || 0)
    })

  if (events.length === 0) {
    return { boundaries: [], segments: [] }
  }

  // Convert each text_span to sentence indices
  const segments = events.map((event, idx) => {
    const { start, end } = event.text_span
    
    // Find sentence indices for start and end
    const startSentIdx = charOffsetToSentenceIndex(fullText, start, sentences)
    const endSentIdx = charOffsetToSentenceIndex(fullText, end - 1, sentences) // end is exclusive
    
    return {
      segmentId: idx + 1,
      startChar: start,
      endChar: end,
      startSentenceIdx: startSentIdx,
      endSentenceIdx: endSentIdx,
      text: event.text_span.text || fullText.substring(start, end),
      eventId: event.id,
      eventType: event.event_type || 'OTHER',
      description: event.description || '',
      timeOrder: event.time_order || idx + 1
    }
  })

  // Build boundaries from segment end positions
  // Boundary i means between sentence i and i+1
  const boundaries = []
  
  // Use a set to avoid duplicates
  const boundarySet = new Set()
  
  for (const segment of segments) {
    // End of segment is a boundary (after endSentenceIdx)
    if (segment.endSentenceIdx >= 0 && segment.endSentenceIdx < sentences.length - 1) {
      boundarySet.add(segment.endSentenceIdx)
    }
  }
  
  // Convert to sorted array
  const sortedBoundaries = Array.from(boundarySet).sort((a, b) => a - b)
  
  return {
    boundaries: sortedBoundaries,
    segments: segments
  }
}

/**
 * Create a mapping of character positions to sentence indices.
 * @param {string} text - Full text
 * @param {Array<string>} sentences - Array of sentences
 * @returns {Array<{start: number, end: number, sentenceIdx: number}>}
 */
export function buildCharToSentenceMapping(text, sentences) {
  const mapping = []
  let currentPos = 0
  
  for (let i = 0; i < sentences.length; i++) {
    const sentenceText = sentences[i].trim()
    if (!sentenceText) continue
    
    // Find the sentence in the original text
    const foundIndex = text.indexOf(sentenceText, currentPos)
    
    if (foundIndex !== -1) {
      mapping.push({
        start: foundIndex,
        end: foundIndex + sentenceText.length,
        sentenceIdx: i
      })
      currentPos = foundIndex + sentenceText.length
    } else {
      // Fallback: use estimated position
      mapping.push({
        start: currentPos,
        end: currentPos + sentenceText.length,
        sentenceIdx: i
      })
      currentPos += sentenceText.length
    }
  }
  
  return mapping
}

/**
 * Build segments from boundaries (similar to groundtruth structure).
 * Boundaries are indices between sentences (boundary i means between sentence i and i+1).
 * @param {Array<number>} boundaries - Array of boundary indices
 * @param {string} text - Full text
 * @param {Array<string>} sentences - Array of sentences
 * @returns {Array<Object>} - Array of segments with {segmentId, startChar, endChar, startSentenceIdx, endSentenceIdx, text}
 */
export function buildSegmentsFromBoundaries(boundaries, text, sentences) {
  if (!boundaries || boundaries.length === 0) {
    // If no boundaries, treat entire text as one segment
    return [{
      segmentId: 1,
      startChar: 0,
      endChar: text.length,
      startSentenceIdx: 0,
      endSentenceIdx: Math.max(0, sentences.length - 1),
      text: text
    }]
  }

  // Build sentence-to-character mapping
  const sentenceMapping = buildCharToSentenceMapping(text, sentences)
  
  // Sort boundaries
  const sortedBoundaries = [...boundaries].sort((a, b) => a - b).filter(b => b >= 0 && b < sentences.length)
  
  const segments = []
  let startSentIdx = 0
  
  for (let i = 0; i <= sortedBoundaries.length; i++) {
    // Boundary i means between sentence i and i+1, so segment ends at sentence i
    // Last segment goes from last boundary+1 to end of sentences
    const endSentIdx = i < sortedBoundaries.length ? sortedBoundaries[i] : sentences.length - 1
    
    if (endSentIdx < startSentIdx) continue
    
    // Find character positions for this segment
    const startMapping = sentenceMapping.find(m => m.sentenceIdx === startSentIdx)
    const endMapping = sentenceMapping.find(m => m.sentenceIdx === endSentIdx)
    
    let startChar = 0
    let endChar = text.length
    
    if (startMapping) {
      startChar = startMapping.start
    }
    
    if (endMapping) {
      // End char is after the end of the last sentence in the segment
      endChar = endMapping.end
      // For non-last segments, we might need to include delimiter after the sentence
      // But for simplicity, use the mapping end which should include the sentence
    } else if (endSentIdx === sentences.length - 1) {
      // Last segment extends to end of text
      endChar = text.length
    }
    
    // Ensure we don't go beyond text length
    endChar = Math.min(endChar, text.length)
    
    // Extract text for this segment
    const segmentText = text.substring(startChar, endChar)
    
    segments.push({
      segmentId: i + 1,
      startChar: startChar,
      endChar: endChar,
      startSentenceIdx: startSentIdx,
      endSentenceIdx: endSentIdx,
      text: segmentText
    })
    
    // Next segment starts after this boundary (at sentence endSentIdx + 1)
    startSentIdx = endSentIdx + 1
  }
  
  return segments
}
