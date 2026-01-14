// Cache utility for storing last used folder and file selection
// Cache is now stored in the parent folder as .annotation_cache.json file
const CACHE_KEY = 'annotation_tool_folder_cache'; // Fallback for localStorage

// Save cache to backend (stored in parent folder as .annotation_cache.json)
export async function saveFolderCache(data) {
  if (!data.folderPath) {
    // Fallback to localStorage if no folderPath
    try {
      localStorage.setItem(CACHE_KEY, JSON.stringify({
        selectedIndex: data.selectedIndex !== undefined ? data.selectedIndex : -1,
        culture: data.culture || null,
        timestamp: Date.now()
      }));
      return true;
    } catch (error) {
      console.error('Failed to save folder cache to localStorage:', error);
      return false;
    }
  }
  
  try {
    const response = await fetch("http://localhost:3001/api/save-cache", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        folderPath: data.folderPath,
        selectedIndex: data.selectedIndex !== undefined ? data.selectedIndex : -1,
        culture: data.culture || null
      })
    });
    
    if (response.ok) {
      const result = await response.json();
      console.log(`[CACHE] Saved cache to folder: ${data.folderPath}`);
      return true;
    } else {
      const error = await response.json();
      console.error('Failed to save cache:', error);
      return false;
    }
  } catch (error) {
    console.error('Failed to save folder cache:', error);
    return false;
  }
}

// Load cache from backend (from parent folder .annotation_cache.json file)
export async function loadFolderCache(folderPath = null) {
  if (folderPath) {
    try {
      const response = await fetch("http://localhost:3001/api/load-cache", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ folderPath })
      });
      
      if (response.ok) {
        const result = await response.json();
        if (result.found && result.data) {
          console.log(`[CACHE] Loaded cache from folder: ${folderPath}`);
          return {
            selectedIndex: result.data.selectedIndex !== undefined ? result.data.selectedIndex : -1,
            culture: result.data.culture || null,
            timestamp: result.data.timestamp || 0
          };
        }
      }
    } catch (error) {
      console.error('Failed to load folder cache from backend:', error);
    }
  }
  
  // Fallback to localStorage
  try {
    const cached = localStorage.getItem(CACHE_KEY);
    if (!cached) return null;
    
    const data = JSON.parse(cached);
    return {
      selectedIndex: data.selectedIndex !== undefined ? data.selectedIndex : -1,
      culture: data.culture || null,
      timestamp: data.timestamp || 0
    };
  } catch (error) {
    console.error('Failed to load folder cache from localStorage:', error);
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
  const paths = fileList
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
    part.toLowerCase() === 'texts' || part.toLowerCase() === 'traditional_texts'
  );
  
  if (textsIndex > 0) {
    // Found texts folder, extract parent folder
    // Example: ["Japanese_test2", "texts"] -> "Japanese_test2"
    const parentParts = pathParts.slice(0, textsIndex);
    const result = parentParts.join('/');
    console.log(`[EXTRACT-PATH] Found texts folder, extracted parent: ${firstPath} -> ${result}`);
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
