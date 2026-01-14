
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

// Helper to resolve folder path relative to project root
// Support arbitrary paths - if path is absolute, use it; otherwise resolve relative to PROJECT_ROOT
const resolveFolderPath = (folderPath) => {
  if (!folderPath || folderPath.trim() === '') {
    return PROJECT_ROOT;
  }
  // If it's an absolute path, use it directly
  if (path.isAbsolute(folderPath)) {
    return folderPath;
  }
  // Otherwise, resolve relative to PROJECT_ROOT
  return path.resolve(PROJECT_ROOT, folderPath);
};

// Validate that folder path contains a texts subfolder
const validateFolderHasTexts = (fullFolderPath) => {
  const textsPath = path.join(fullFolderPath, 'texts');
  const traditionalTextsPath = path.join(fullFolderPath, 'traditional_texts');
  return fs.existsSync(textsPath) || fs.existsSync(traditionalTextsPath);
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
    // Resolve it to absolute path
    const fullFolderPath = resolveFolderPath(folderPath);
    
    console.log(`[SAVE] folderPath: ${folderPath}, fileName: ${fileName}, version: ${version}`);
    console.log(`[SAVE] Resolved fullFolderPath: ${fullFolderPath}`);
    
    // Validate: folder must contain texts subfolder
    if (!validateFolderHasTexts(fullFolderPath)) {
      return res.status(400).json({ 
        error: `Folder does not contain "texts" or "traditional_texts" subfolder: ${fullFolderPath}` 
      });
    }
    
    // Create json folder name based on version
    const targetDirName = version === 'v3' ? 'json_v3' : (version === 'v2' ? 'json_v2' : 'json');
    
    // Create target directory: json folders are in the parent folder (same level as texts)
    const targetDir = path.join(fullFolderPath, targetDirName);

    // Ensure target directory exists
    try {
      fs.mkdirSync(targetDir, { recursive: true });
    } catch (err) {
      console.error(`Failed to create directory ${targetDir}:`, err);
      return res.status(500).json({ error: 'Failed to create directory' });
    }

    // Create file name with suffix
    const suffix = version === 'v3' ? '_v3' : (version === 'v2' ? '_v2' : '');
    const targetFileName = `${fileName}${suffix}.json`;
    const targetPath = path.join(targetDir, targetFileName);

    try {
      fs.writeFileSync(targetPath, JSON.stringify(content, null, 2));
      res.json({ success: true, path: targetPath });
    } catch (err) {
      console.error(`Error writing file ${targetPath}:`, err);
      res.status(500).json({ error: 'Failed to write file: ' + err.message });
    }
  } catch (err) {
    console.error('Error in /api/save:', err);
    res.status(500).json({ error: 'Internal server error: ' + err.message });
  }
});

app.post('/api/load', (req, res) => {
  const { folderPath, fileName, originalPath } = req.body;
  
  let fullFolderPath = null;
  let targetFileName = null;
  
  // Use folderPath and fileName directly
  if (folderPath && fileName) {
    // folderPath is the parent folder that contains texts subfolder
    fullFolderPath = resolveFolderPath(folderPath);
    targetFileName = fileName;
    
    console.log(`[LOAD] folderPath: ${folderPath}, fileName: ${fileName}`);
    console.log(`[LOAD] Resolved fullFolderPath: ${fullFolderPath}`);
    
    // Validate: folder must contain texts subfolder
    if (!validateFolderHasTexts(fullFolderPath)) {
      return res.status(400).json({ 
        error: `Folder does not contain "texts" or "traditional_texts" subfolder: ${fullFolderPath}` 
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
      part.toLowerCase() === 'texts' || part.toLowerCase() === 'traditional_texts'
    );
    
    if (textsIndex > 0) {
      // Extract parent folder before texts
      baseFolderPath = pathParts.slice(0, textsIndex).join('/');
    }
    
    fullFolderPath = resolveFolderPath(baseFolderPath);
    
    // Validate
    if (!validateFolderHasTexts(fullFolderPath)) {
      return res.json({ found: false, error: 'Invalid folder structure' });
    }
  } else {
    return res.status(400).json({ error: 'Missing folderPath+fileName or originalPath' });
  }
  
  // Try to find JSON files in json_v3, json_v2, json folders
  // These folders are in the parent folder (same level as texts)
  const candidates = [];
  const jsonFolders = ['json_v3', 'json_v2', 'json'];
  const versions = [3, 2, 1];
  
  for (let i = 0; i < jsonFolders.length; i++) {
    const jsonFolder = jsonFolders[i];
    const version = versions[i];
    const jsonDir = path.join(fullFolderPath, jsonFolder);
    
    if (fs.existsSync(jsonDir)) {
      // Try with suffix first (e.g., jp_003_v3.json)
      candidates.push({ path: path.join(jsonDir, `${targetFileName}_v${version}.json`), version });
      // Then without suffix (e.g., jp_003.json)
      candidates.push({ path: path.join(jsonDir, `${targetFileName}.json`), version });
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
    
    // Resolve the folder path
    const fullFolderPath = resolveFolderPath(folderPath);
    
    // Validate: folder must contain texts subfolder
    if (!validateFolderHasTexts(fullFolderPath)) {
      return res.status(400).json({ 
        error: `Folder does not contain "texts" or "traditional_texts" subfolder: ${fullFolderPath}` 
      });
    }
    
    // Create cache file in the parent folder
    const cachePath = path.join(fullFolderPath, '.annotation_cache.json');
    const cacheData = {
      selectedIndex: selectedIndex !== undefined ? selectedIndex : -1,
      culture: culture || null,
      timestamp: Date.now()
    };
    
    try {
      fs.writeFileSync(cachePath, JSON.stringify(cacheData, null, 2));
      console.log(`[CACHE] Saved cache to: ${cachePath}`);
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
    
    // Resolve the folder path
    const fullFolderPath = resolveFolderPath(folderPath);
    
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
