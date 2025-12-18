// Cache utility for storing last used folder and file selection
const CACHE_KEY = 'annotation_tool_folder_cache';

export function saveFolderCache(data) {
  try {
    const cacheData = {
      folderPath: data.folderPath || null,
      selectedIndex: data.selectedIndex !== undefined ? data.selectedIndex : -1,
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

export function loadFolderCache() {
  try {
    const cached = localStorage.getItem(CACHE_KEY);
    if (!cached) return null;
    
    const data = JSON.parse(cached);
    return {
      folderPath: data.folderPath || null,
      selectedIndex: data.selectedIndex !== undefined ? data.selectedIndex : -1,
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

// Extract folder path from file paths
export function extractFolderPath(fileList) {
  if (!fileList || fileList.length === 0) return null;
  
  // Get the first file's path
  const firstFile = fileList[0];
  const path = firstFile.webkitRelativePath || firstFile.name;
  
  if (!path) return null;
  
  // Extract directory path (everything except the filename)
  const parts = path.split('/');
  if (parts.length > 1) {
    parts.pop(); // Remove filename
    return parts.join('/');
  }
  
  return null;
}
