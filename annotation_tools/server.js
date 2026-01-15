
import express from 'express';
import cors from 'cors';
import bodyParser from 'body-parser';
import fs from 'fs';
import path from 'path';
import os from 'os';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = 3001;

// Middleware
// Configure CORS to allow requests from the dev server
app.use(cors({
  origin: function (origin, callback) {
    // Allow requests with no origin (like mobile apps, curl, or sendBeacon)
    if (!origin) return callback(null, true);
    // Allow localhost with any port
    if (origin.match(/^http:\/\/localhost:\d+$/)) {
      return callback(null, true);
    }
    // Allow specific origins
    const allowedOrigins = ['http://localhost:5177', 'http://localhost:5173', 'http://localhost:3000'];
    if (allowedOrigins.indexOf(origin) !== -1) {
      return callback(null, true);
    }
    callback(null, true); // Allow all for development
  },
  credentials: false, // sendBeacon doesn't send credentials by default
  methods: ['GET', 'POST', 'OPTIONS'],
  allowedHeaders: ['Content-Type']
}));
// Handle JSON requests (from XHR, fetch)
app.use(bodyParser.json({ limit: '50mb' }));
// Handle plain text (from sendBeacon - sends JSON as text/plain to avoid preflight)
app.use(bodyParser.text({ type: 'text/plain', limit: '50mb' }));

// We assume this server is running in `annotation_tools/`
const PROJECT_ROOT = path.resolve(__dirname, '..');

console.log(`Server running. Project root: ${PROJECT_ROOT}`);

// Helper to resolve folder path
// Simple logic: assume user-selected folders are in PROJECT_ROOT/datasets/
// If absolute path is provided, use it directly
// Otherwise, resolve as PROJECT_ROOT/datasets/{folderPath}
const resolveFolderPath = (folderPath) => {
  if (!folderPath || folderPath.trim() === '') {
    throw new Error('Folder path is empty');
  }
  
  // If it's an absolute path, use it directly
  if (path.isAbsolute(folderPath)) {
    return folderPath;
  }
  
  // Otherwise, assume it's in datasets/ folder
  const resolvedPath = path.join(PROJECT_ROOT, 'datasets', folderPath);
  
  // Check if the folder exists
  if (!fs.existsSync(resolvedPath)) {
    throw new Error(`Folder not found in datasets/: ${folderPath} -> ${resolvedPath}`);
  }
  
  return resolvedPath;
};

// Validate that folder path contains a texts subfolder
const validateFolderHasTexts = (fullFolderPath) => {
  const textsPath = path.join(fullFolderPath, 'texts');
  return fs.existsSync(textsPath);
};

// Handle CORS preflight requests
app.options('/api/save', (req, res) => {
  const origin = req.headers.origin;
  // Allow localhost with any port
  if (origin && origin.match(/^http:\/\/localhost:\d+$/)) {
    res.header('Access-Control-Allow-Origin', origin);
  } else {
    res.header('Access-Control-Allow-Origin', origin || '*');
  }
  res.header('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type');
  // Don't set Access-Control-Allow-Credentials - we don't use credentials
  res.sendStatus(200);
});

app.post('/api/save', (req, res) => {
  try {
    // Set CORS headers explicitly
    const origin = req.headers.origin;
    if (origin && origin.match(/^http:\/\/localhost:\d+$/)) {
      res.header('Access-Control-Allow-Origin', origin);
    }
    
    // Handle different request formats:
    // 1. JSON object (from XHR/fetch) - Content-Type: application/json
    // 2. Plain text JSON string (from sendBeacon) - Content-Type: text/plain
    let body = req.body;
    
    // If body is a string (from sendBeacon sending text/plain), parse it as JSON
    if (typeof body === 'string') {
      try {
        body = JSON.parse(body);
      } catch (err) {
        console.error('Failed to parse request body as JSON:', err);
        return res.status(400).json({ error: 'Invalid JSON in request body: ' + err.message });
      }
    }

    if (!body || typeof body !== 'object') {
      return res.status(400).json({ error: 'Invalid request body format' });
    }

    const { folderPath, fileName, content, version } = body;
    
    if (!folderPath || !fileName || !content) {
      return res.status(400).json({ error: 'Missing folderPath, fileName, or content' });
    }

    // folderPath is the parent folder that contains texts subfolder
    // Resolve it to absolute path (assumes folder is in datasets/)
    let fullFolderPath;
    try {
      fullFolderPath = resolveFolderPath(folderPath);
    } catch (err) {
      console.error(`[SAVE] Failed to resolve folder path: ${err.message}`);
      return res.status(400).json({ error: err.message });
    }
    
    console.log(`[SAVE] folderPath: ${folderPath}, fileName: ${fileName}, version: ${version}`);
    console.log(`[SAVE] Resolved fullFolderPath: ${fullFolderPath}`);
    
    // Validate: folder must contain texts subfolder
    if (!validateFolderHasTexts(fullFolderPath)) {
      return res.status(400).json({ 
        error: `Folder does not contain "texts" subfolder: ${fullFolderPath}` 
      });
    }
    
    // Create json folder name based on version
    const targetDirName = version === 'v3' ? 'json_v3' : (version === 'v2' ? 'json_v2' : 'json');
    
    // Create target directory: json folders are in the parent folder (same level as texts)
    const targetDir = path.join(fullFolderPath, targetDirName);
    
    console.log(`[SAVE] Target directory: ${targetDir}`);
    console.log(`[SAVE] Parent folder exists: ${fs.existsSync(fullFolderPath)}`);
    console.log(`[SAVE] Texts folder exists: ${fs.existsSync(path.join(fullFolderPath, 'texts'))}`);

    // Ensure target directory exists
    try {
      fs.mkdirSync(targetDir, { recursive: true });
      console.log(`[SAVE] Directory created/verified: ${targetDir}`);
    } catch (err) {
      console.error(`[SAVE] Failed to create directory ${targetDir}:`, err);
      return res.status(500).json({ error: 'Failed to create directory: ' + err.message });
    }

    // Create file name with suffix
    const suffix = version === 'v3' ? '_v3' : (version === 'v2' ? '_v2' : '');
    const targetFileName = `${fileName}${suffix}.json`;
    const targetPath = path.join(targetDir, targetFileName);
    
    console.log(`[SAVE] Target file path: ${targetPath}`);
    console.log(`[SAVE] Content size: ${JSON.stringify(content).length} bytes`);

    try {
      fs.writeFileSync(targetPath, JSON.stringify(content, null, 2));
      console.log(`[SAVE] Successfully saved to: ${targetPath}`);
      const stats = fs.statSync(targetPath);
      console.log(`[SAVE] File written, size: ${stats.size} bytes`);
      res.json({ success: true, path: targetPath });
    } catch (err) {
      console.error(`[SAVE] Error writing file ${targetPath}:`, err);
      res.status(500).json({ error: 'Failed to write file: ' + err.message });
    }
  } catch (err) {
    console.error('Error in /api/save:', err);
    res.status(500).json({ error: 'Internal server error: ' + err.message });
  }
});

app.post('/api/load', (req, res) => {
  const { folderPath, fileName, originalPath, version } = req.body;
  
  let fullFolderPath = null;
  let targetFileName = null;
  
  // Use folderPath and fileName directly
  if (folderPath && fileName) {
    // folderPath is the parent folder that contains texts subfolder
    // Resolve it to absolute path (assumes folder is in datasets/)
    try {
      fullFolderPath = resolveFolderPath(folderPath);
    } catch (err) {
      console.error(`[LOAD] Failed to resolve folder path: ${err.message}`);
      return res.status(400).json({ error: err.message });
    }
    targetFileName = fileName;
    
    console.log(`[LOAD] folderPath: ${folderPath}, fileName: ${fileName}`);
    console.log(`[LOAD] Resolved fullFolderPath: ${fullFolderPath}`);
    
    // Validate: folder must contain texts subfolder
    if (!validateFolderHasTexts(fullFolderPath)) {
      return res.status(400).json({ 
        error: `Folder does not contain "texts" subfolder: ${fullFolderPath}` 
      });
    }
  } 
  // Fallback: extract from originalPath (for backward compatibility)
  else if (originalPath) {
    const pathParts = originalPath.split('/');
    targetFileName = path.basename(originalPath, path.extname(originalPath));
    
    // Extract parent folder from originalPath
    // Example: originalPath="Japanese_test2/texts/file.txt" -> extract "Japanese_test2"
    let baseFolderPath = pathParts.slice(0, -1).join('/');
    
    // Find texts folder in the path
    const textsIndex = pathParts.findIndex(part => 
      part.toLowerCase() === 'texts'
    );
    
    if (textsIndex > 0) {
      // Extract parent folder before texts
      baseFolderPath = pathParts.slice(0, textsIndex).join('/');
    }
    
    try {
      fullFolderPath = resolveFolderPath(baseFolderPath);
    } catch (err) {
      console.error(`[LOAD] Failed to resolve folder path from originalPath: ${err.message}`);
      return res.json({ found: false, error: err.message });
    }
    
    // Validate
    if (!validateFolderHasTexts(fullFolderPath)) {
      return res.json({ found: false, error: 'Invalid folder structure' });
    }
  } else {
    return res.status(400).json({ error: 'Missing folderPath+fileName or originalPath' });
  }
  
  // If version is specified, only load that version
  if (version === 3 || version === 2) {
    const jsonFolder = version === 3 ? 'json_v3' : 'json_v2';
    const jsonDir = path.join(fullFolderPath, jsonFolder);
    
    if (fs.existsSync(jsonDir)) {
      // Try with suffix first (e.g., jp_003_v3.json)
      const candidates = [
        path.join(jsonDir, `${targetFileName}_v${version}.json`),
        path.join(jsonDir, `${targetFileName}.json`)
      ];
      
      for (const candidatePath of candidates) {
        if (fs.existsSync(candidatePath)) {
          try {
            const content = JSON.parse(fs.readFileSync(candidatePath, 'utf8'));
            return res.json({ found: true, content, version, path: candidatePath });
          } catch (err) {
            console.error(`Error reading/parsing ${candidatePath}:`, err);
          }
        }
      }
    }
    return res.json({ found: false });
  }
  
  // If no version specified, try to find JSON files in json_v3, json_v2 folders (skip json/v1)
  // These folders are in the parent folder (same level as texts)
  // Load v3 first (default), fallback to v2 if v3 doesn't exist, never load v1
  const candidates = [];
  const jsonFolders = ['json_v3', 'json_v2'];
  const versions = [3, 2];
  
  for (let i = 0; i < jsonFolders.length; i++) {
    const jsonFolder = jsonFolders[i];
    const v = versions[i];
    const jsonDir = path.join(fullFolderPath, jsonFolder);
    
    if (fs.existsSync(jsonDir)) {
      // Try with suffix first (e.g., jp_003_v3.json)
      candidates.push({ path: path.join(jsonDir, `${targetFileName}_v${v}.json`), version: v });
      // Then without suffix (e.g., jp_003.json)
      candidates.push({ path: path.join(jsonDir, `${targetFileName}.json`), version: v });
    }
  }
  
  // Try to find first existing candidate
  for (const cand of candidates) {
    if (fs.existsSync(cand.path)) {
      console.log(`Loading JSON from: ${cand.path}`);
      try {
        const content = JSON.parse(fs.readFileSync(cand.path, 'utf8'));
        return res.json({ found: true, content, version: cand.version, path: cand.path });
      } catch (err) {
        console.error(`Error reading/parsing ${cand.path}:`, err);
      }
    }
  }

  return res.json({ found: false });
});

// API endpoint to save cache (last processed position, etc.)
app.post('/api/save-cache', (req, res) => {
  try {
    const origin = req.headers.origin;
    if (origin && origin.match(/^http:\/\/localhost:\d+$/)) {
      res.header('Access-Control-Allow-Origin', origin);
    }
    
    const { folderPath, selectedIndex, culture } = req.body;
    
    if (!folderPath) {
      return res.status(400).json({ error: 'Missing folderPath' });
    }
    
    // Resolve the folder path (assumes folder is in datasets/)
    let fullFolderPath;
    try {
      fullFolderPath = resolveFolderPath(folderPath);
    } catch (err) {
      console.error(`[SAVE-CACHE] Failed to resolve folder path: ${err.message}`);
      return res.status(400).json({ error: err.message });
    }
    
    // Validate: folder must contain texts subfolder
    if (!validateFolderHasTexts(fullFolderPath)) {
      return res.status(400).json({ 
        error: `Folder does not contain "texts" subfolder: ${fullFolderPath}` 
      });
    }
    
    // Create cache file in the parent folder
    const cachePath = path.join(fullFolderPath, '.annotation_cache.json');
    
    // If selectedIndex is undefined, try to preserve existing value from cache
    let selectedIndexToSave = selectedIndex;
    if (selectedIndexToSave === undefined) {
      try {
        if (fs.existsSync(cachePath)) {
          const existingCache = JSON.parse(fs.readFileSync(cachePath, 'utf8'));
          if (existingCache.selectedIndex !== undefined && existingCache.selectedIndex >= 0) {
            selectedIndexToSave = existingCache.selectedIndex;
            console.log(`[CACHE] Preserving existing selectedIndex: ${selectedIndexToSave}`);
          }
        }
      } catch (err) {
        console.warn(`[CACHE] Could not read existing cache to preserve selectedIndex:`, err);
      }
    }
    
    // Only use -1 as fallback if we still don't have a valid index
    if (selectedIndexToSave === undefined || selectedIndexToSave < 0) {
      selectedIndexToSave = -1;
    }
    
    const cacheData = {
      selectedIndex: selectedIndexToSave,
      culture: culture || null,
      timestamp: Date.now()
    };
    
    try {
      fs.writeFileSync(cachePath, JSON.stringify(cacheData, null, 2));
      console.log(`[CACHE] Saved cache to: ${cachePath}, selectedIndex: ${selectedIndexToSave}`);
      return res.json({ success: true, path: cachePath });
    } catch (err) {
      console.error(`Failed to write cache file:`, err);
      return res.status(500).json({ error: 'Failed to write cache file: ' + err.message });
    }
  } catch (err) {
    console.error('Error in /api/save-cache:', err);
    return res.status(500).json({ error: 'Internal server error: ' + err.message });
  }
});

// API endpoint to load cache
app.post('/api/load-cache', (req, res) => {
  try {
    const origin = req.headers.origin;
    if (origin && origin.match(/^http:\/\/localhost:\d+$/)) {
      res.header('Access-Control-Allow-Origin', origin);
    }
    
    const { folderPath } = req.body;
    
    if (!folderPath) {
      return res.status(400).json({ error: 'Missing folderPath' });
    }
    
    // Resolve the folder path (assumes folder is in datasets/)
    let fullFolderPath;
    try {
      fullFolderPath = resolveFolderPath(folderPath);
    } catch (err) {
      console.error(`[LOAD-CACHE] Failed to resolve folder path: ${err.message}`);
      return res.json({ found: false, error: err.message });
    }
    
    // Validate: folder must contain texts subfolder
    if (!validateFolderHasTexts(fullFolderPath)) {
      return res.json({ found: false, error: 'Invalid folder structure' });
    }
    
    // Try to load cache file from the parent folder
    const cachePath = path.join(fullFolderPath, '.annotation_cache.json');
    
    if (!fs.existsSync(cachePath)) {
      return res.json({ found: false });
    }
    
    try {
      const cacheData = JSON.parse(fs.readFileSync(cachePath, 'utf8'));
      console.log(`[CACHE] Loaded cache from: ${cachePath}`);
      return res.json({ found: true, data: cacheData });
    } catch (err) {
      console.error(`Failed to read/parse cache file:`, err);
      return res.json({ found: false, error: 'Failed to read cache file' });
    }
  } catch (err) {
    console.error('Error in /api/load-cache:', err);
    return res.status(500).json({ error: 'Internal server error: ' + err.message });
  }
});

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
