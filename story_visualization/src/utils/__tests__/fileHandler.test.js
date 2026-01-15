/**
 * Tests for fileHandler.js
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { organizeFiles } from '../fileHandler'

describe('organizeFiles', () => {
  it('should organize text files from texts folder', () => {
    const fileList = [
      { name: 'story1.txt', webkitRelativePath: 'texts/story1.txt' },
      { name: 'story2.txt', webkitRelativePath: 'texts/story2.txt' },
    ]
    
    const result = organizeFiles(fileList)
    
    expect(result.texts).toHaveLength(2)
    expect(result.texts[0].id).toBe('story1')
    expect(result.texts[1].id).toBe('story2')
  })

  it('should organize JSON files from json folders', () => {
    const fileList = [
      { name: 'story1.txt', webkitRelativePath: 'texts/story1.txt' },
      { name: 'story1_v2.json', webkitRelativePath: 'json_v2/story1_v2.json' },
      { name: 'story1_v3.json', webkitRelativePath: 'json_v3/story1_v3.json' },
    ]
    
    const result = organizeFiles(fileList)
    
    expect(result.texts).toHaveLength(1)
    expect(result.v2Jsons.story1).toBeDefined()
    expect(result.v3Jsons.story1).toBeDefined()
  })

  it('should skip JSON files in texts folder', () => {
    const fileList = [
      { name: 'story1.txt', webkitRelativePath: 'texts/story1.txt' },
      { name: 'config.json', webkitRelativePath: 'texts/config.json' },
    ]
    
    const result = organizeFiles(fileList)
    
    expect(result.texts).toHaveLength(1)
    expect(Object.keys(result.v2Jsons)).toHaveLength(0)
    expect(Object.keys(result.v3Jsons)).toHaveLength(0)
  })

  it('should handle files without webkitRelativePath', () => {
    const fileList = [
      { name: 'story1.txt' },
    ]
    
    const result = organizeFiles(fileList)
    
    // Should handle gracefully (may not match without path)
    expect(result).toBeDefined()
  })

  it('should extract correct IDs from filenames', () => {
    const fileList = [
      { name: 'CH_002_牛郎织女.txt', webkitRelativePath: 'texts/CH_002_牛郎织女.txt' },
      { name: 'FA_001_v2.json', webkitRelativePath: 'json_v2/FA_001_v2.json' },
    ]
    
    const result = organizeFiles(fileList)
    
    expect(result.texts[0].id).toBe('CH_002_牛郎织女')
    expect(result.v2Jsons.FA_001).toBeDefined()
  })
})
