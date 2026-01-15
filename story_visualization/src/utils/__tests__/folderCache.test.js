/**
 * Tests for folderCache.js
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { saveFolderCache, loadFolderCache, clearFolderCache, extractFolderPath } from '../folderCache'

describe('folderCache', () => {
  beforeEach(() => {
    clearFolderCache()
  })

  afterEach(() => {
    clearFolderCache()
  })

  it('should save and load folder cache', () => {
    const data = {
      folderPath: 'ChineseTales',
      selectedIndex: 2,
      culture: 'Chinese'
    }
    
    saveFolderCache(data)
    const loaded = loadFolderCache()
    
    expect(loaded).toBeDefined()
    expect(loaded.folderPath).toBe('ChineseTales')
    expect(loaded.selectedIndex).toBe(2)
    expect(loaded.culture).toBe('Chinese')
  })

  it('should handle missing cache gracefully', () => {
    const loaded = loadFolderCache()
    // Should return null if no cache exists
    expect(loaded).toBeNull()
  })

  it('should clear cache', () => {
    saveFolderCache({ folderPath: 'test', selectedIndex: 0, culture: 'Chinese' })
    clearFolderCache()
    const loaded = loadFolderCache()
    expect(loaded).toBeNull()
  })

  it('should extract folder path from file list', () => {
    const fileList = [
      { webkitRelativePath: 'ChineseTales/texts/story1.txt' },
      { webkitRelativePath: 'ChineseTales/texts/story2.txt' },
    ]
    
    const folderPath = extractFolderPath(fileList)
    
    expect(folderPath).toBe('ChineseTales')
  })

  it('should handle files without paths', () => {
    const fileList = [
      { name: 'story1.txt' },
    ]
    
    const folderPath = extractFolderPath(fileList, 'fallback')
    
    expect(folderPath).toBe('fallback')
  })

  it('should handle nested paths correctly', () => {
    const fileList = [
      { webkitRelativePath: 'datasets/ChineseTales/texts/CH_001.txt' },
    ]
    
    const folderPath = extractFolderPath(fileList)
    
    expect(folderPath).toBe('datasets/ChineseTales')
  })
})
