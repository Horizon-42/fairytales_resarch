
import express from 'express';
import cors from 'cors';
import bodyParser from 'body-parser';
import fs from 'fs';
import path from 'path';
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

// Helper to find file recursively in datasets if not found directly
const findFileInDatasets = (targetName, searchDir) => {
  if (!fs.existsSync(searchDir)) return null;
  const entries = fs.readdirSync(searchDir, { withFileTypes: true });
  
  for (const entry of entries) {
    const fullPath = path.join(searchDir, entry.name);
    if (entry.isDirectory()) {
      // Skip node_modules or .git or json folders to optimize
      if (entry.name === 'node_modules' || entry.name.startsWith('.')) continue;
      
      const res = findFileInDatasets(targetName, fullPath);
      if (res) return res;
    } else if (entry.isFile() && entry.name === targetName) {
      return fullPath;
    }
  }
  return null;
};

// Helper to resolve the correct file path
const resolveFilePath = (originalPath) => {
  // Strategy A: PROJECT_ROOT + /originalPath (Exact relative match)
  let fullPath = path.join(PROJECT_ROOT, originalPath);
  if (fs.existsSync(fullPath)) return fullPath;

  // Strategy B: PROJECT_ROOT + /datasets/ + originalPath
  const inDatasets = path.join(PROJECT_ROOT, 'datasets', originalPath);
  if (fs.existsSync(inDatasets)) return inDatasets;

  // Strategy C: Recursive search in datasets for the filename
  const fileName = path.basename(originalPath);
  const foundPath = findFileInDatasets(fileName, path.join(PROJECT_ROOT, 'datasets'));
  
  if (foundPath) {
    console.log(`Resolved ${originalPath} to ${foundPath}`);
    return foundPath;
  }

  // Fallback: Return Strategy A path even if it doesn't exist (to create new structure)
  return fullPath;
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
    // Don't set Access-Control-Allow-Credentials - we don't use credentials
    
    // Debug: log what we received
    console.log('Received save request - Content-Type:', req.headers['content-type']);
    console.log('Body type:', typeof req.body);
    console.log('Body keys:', req.body ? Object.keys(req.body) : 'null');
    if (req.body && req.body.data) {
      console.log('FormData data type:', typeof req.body.data);
      console.log('FormData data length:', req.body.data ? req.body.data.length : 0);
    }
    
    // Handle different request formats:
    // 1. JSON object (from XHR/fetch) - Content-Type: application/json
    // 2. Plain text JSON string (from sendBeacon) - Content-Type: text/plain
    let body = req.body;
    
    // If body is a string (from sendBeacon sending text/plain), parse it as JSON
    if (typeof body === 'string') {
      try {
        body = JSON.parse(body);
        console.log('Parsed text/plain body as JSON');
      } catch (err) {
        console.error('Failed to parse text body as JSON:', err);
        console.error('Data content (first 200 chars):', body.substring(0, 200));
        return res.status(400).json({ error: 'Invalid JSON in request body: ' + err.message });
      }
    }

    if (!body || typeof body !== 'object') {
      console.error('Invalid body after parsing:', body);
      return res.status(400).json({ error: 'Invalid request body format' });
    }

    const { originalPath, content, version } = body;
    
    if (!originalPath || !content) {
      console.error('Missing required fields:', { originalPath: !!originalPath, content: !!content });
      return res.status(400).json({ error: 'Missing originalPath or content' });
    }

    const fullOriginalPath = resolveFilePath(originalPath);
  const fileDir = path.dirname(fullOriginalPath);
  const fileName = path.basename(fullOriginalPath, path.extname(fullOriginalPath));

  let targetDirName = version === 'v2' ? 'json_v2' : 'json';
  let targetDir;

  const parentDir = path.dirname(fileDir);
  const currentDirName = path.basename(fileDir);

  if (currentDirName === 'texts' || currentDirName === 'traditional_texts') {
    // Standard structure: Category/texts -> Category/json
    targetDir = path.join(parentDir, targetDirName);
  } else {
     targetDir = path.join(fileDir, targetDirName);
  }

  // Ensure target directory exists
  try {
    fs.mkdirSync(targetDir, { recursive: true });
  } catch (err) {
    console.error(`Failed to create directory ${targetDir}:`, err);
    return res.status(500).json({ error: 'Failed to create directory' });
  }

  const suffix = version === 'v2' ? '_v2' : '';
  const targetFileName = `${fileName}${suffix}.json`;
  const targetPath = path.join(targetDir, targetFileName);

  console.log(`Saving to: ${targetPath}`);

    try {
      fs.writeFileSync(targetPath, JSON.stringify(content, null, 2));
      res.json({ success: true, path: targetPath });
    } catch (err) {
      console.error(`Error writing file ${targetPath}:`, err);
      res.status(500).json({ error: 'Failed to write file: ' + err.message });
    }
  } catch (err) {
    console.error('Unexpected error in /api/save:', err);
    console.error('Error stack:', err.stack);
    res.status(500).json({ error: 'Internal server error: ' + err.message });
  }
});

app.post('/api/load', (req, res) => {
  const { originalPath } = req.body;
  
  if (!originalPath) {
    return res.status(400).json({ error: 'Missing originalPath' });
  }

  const fullOriginalPath = resolveFilePath(originalPath);
  
  const fileDir = path.dirname(fullOriginalPath);
  const fileName = path.basename(fullOriginalPath, path.extname(fullOriginalPath));
  const parentDir = path.dirname(fileDir);
  const currentDirName = path.basename(fileDir);

  const candidates = [];
  
  // Sibling folder strategy (datasets/Category/texts -> datasets/Category/json_v2)
  if (currentDirName === 'texts' || currentDirName === 'traditional_texts') {
    candidates.push({ path: path.join(parentDir, 'json_v2', `${fileName}_v2.json`), version: 2 });
    candidates.push({ path: path.join(parentDir, 'json_v2', `${fileName}.json`), version: 2 });
    candidates.push({ path: path.join(parentDir, 'json', `${fileName}.json`), version: 1 });
    candidates.push({ path: path.join(parentDir, 'json', `${fileName}_v1.json`), version: 1 });
  } else {
    // Nested strategy (MyStory/texts -> MyStory/json_v2)
    candidates.push({ path: path.join(fileDir, 'json_v2', `${fileName}_v2.json`), version: 2 });
    candidates.push({ path: path.join(fileDir, 'json_v2', `${fileName}.json`), version: 2 });
    candidates.push({ path: path.join(fileDir, 'json', `${fileName}.json`), version: 1 });
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

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
