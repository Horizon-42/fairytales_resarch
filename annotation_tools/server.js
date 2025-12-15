
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
app.use(cors());
app.use(bodyParser.json({ limit: '50mb' }));

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

app.post('/api/save', (req, res) => {
  const { originalPath, content, version } = req.body;

  if (!originalPath || !content) {
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
    res.status(500).json({ error: 'Failed to write file' });
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
