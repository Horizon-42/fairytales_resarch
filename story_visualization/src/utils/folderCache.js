// Cache utility for storing last used folder and file selection
const CACHE_KEY = 'story_visualization_folder_cache';

// Save cache to localStorage
export function saveFolderCache(data) {
  try {
    const cacheData = {
      selectedIndex: data.selectedIndex !== undefined ? data.selectedIndex : -1,
      folderPath: data.folderPath || null,
      culture: data.culture || null,
      timestamp: Date.now()
    };
    localStorage.setItem(CACHE_KEY, JSON.stringify(cacheData));
    return true;
  } catch (error) {
    console.error('Failed to save folder cache:', error);
    return false;
  }
}

// Load cache from localStorage
export function loadFolderCache() {
  try {
    const cached = localStorage.getItem(CACHE_KEY);
    if (!cached) return null;
    
    const data = JSON.parse(cached);
    return {
      selectedIndex: data.selectedIndex !== undefined ? data.selectedIndex : -1,
      folderPath: data.folderPath || null,
      culture: data.culture || null,
      timestamp: data.timestamp || 0
    };
  } catch (error) {
    console.error('Failed to load folder cache:', error);
    return null;
  }
}

export function clearFolderCache() {
  try {
    localStorage.removeItem(CACHE_KEY);
    return true;
  } catch (error) {
    console.error('Failed to clear folder cache:', error);
    return false;
  }
}

// Extract parent folder path from file paths
// User must select the parent folder that contains "texts" subfolder
// Files will be in paths like: "Japanese_test2/texts/file.txt"
// We extract "Japanese_test2" as the parent folder path
export function extractFolderPath(fileList, fallbackFolderPath = null) {
  if (!fileList || fileList.length === 0) return fallbackFolderPath;
  
  // Get paths from all files
  const paths = Array.from(fileList)
    .map(file => file.webkitRelativePath || file.name)
    .filter(path => path && path.includes('/'));
  
  if (paths.length === 0) {
    // No subdirectories - user might have selected texts folder directly (should be prevented)
    return fallbackFolderPath;
  }
  
  // Find the parent folder that contains texts
  // File paths are like: "Japanese_test2/texts/file.txt" or "texts/file.txt"
  const firstPath = paths[0];
  const pathParts = firstPath.split('/');
  
  // Remove filename (last part)
  pathParts.pop();
  
  // Find texts folder in the path
  const textsIndex = pathParts.findIndex(part => 
    part.toLowerCase() === 'texts'
  );
  
  if (textsIndex > 0) {
    // Found texts folder, extract parent folder
    // Example: ["Japanese_test2", "texts"] -> "Japanese_test2"
    const parentParts = pathParts.slice(0, textsIndex);
    const result = parentParts.join('/');
    return result;
  } else if (textsIndex === 0) {
    // texts is the first part - user selected texts folder directly (should be prevented)
    console.warn(`[EXTRACT-PATH] texts folder is first part, should select parent folder instead`);
    return fallbackFolderPath;
  } else {
    // No texts folder found in path - use fallback
    console.warn(`[EXTRACT-PATH] No texts folder found in path: ${firstPath}`);
    return fallbackFolderPath;
  }
}
