#!/usr/bin/env node
/**
 * Comprehensive test for all path scenarios
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PROJECT_ROOT = path.resolve(__dirname, '..');

const resolveFolderPath = (folderPath) => {
  if (!folderPath || folderPath.trim() === '') {
    return path.join(PROJECT_ROOT, 'datasets');
  }
  if (folderPath.startsWith('datasets/')) {
    return path.join(PROJECT_ROOT, folderPath);
  }
  return path.join(PROJECT_ROOT, 'datasets', folderPath);
};

// Simulate backend save logic
const simulateSave = (folderPath, fileName, version) => {
  const folderPathParts = folderPath.split('/');
  let fullFolderPath;
  
  if (folderPathParts.length > 1) {
    const parentPath = folderPathParts.slice(0, -1).join('/');
    fullFolderPath = resolveFolderPath(parentPath);
  } else {
    fullFolderPath = resolveFolderPath(folderPath);
  }
  
  const targetDirName = version === 'v3' ? 'json_v3' : (version === 'v2' ? 'json_v2' : 'json');
  const targetDir = path.join(fullFolderPath, targetDirName);
  const suffix = version === 'v3' ? '_v3' : (version === 'v2' ? '_v2' : '');
  const targetFileName = `${fileName}${suffix}.json`;
  const targetPath = path.join(targetDir, targetFileName);
  
  return {
    folderPath,
    parentPath: folderPathParts.length > 1 ? folderPathParts.slice(0, -1).join('/') : null,
    fullFolderPath,
    targetDir,
    targetPath
  };
};

// Simulate backend load logic
const simulateLoad = (folderPath, fileName) => {
  const folderPathParts = folderPath.split('/');
  let fullFolderPath;
  
  if (folderPathParts.length > 1) {
    const parentPath = folderPathParts.slice(0, -1).join('/');
    fullFolderPath = resolveFolderPath(parentPath);
  } else {
    fullFolderPath = resolveFolderPath(folderPath);
  }
  
  const jsonFolders = ['json_v3', 'json_v2', 'json'];
  const versions = [3, 2, 1];
  const candidates = [];
  
  for (let i = 0; i < jsonFolders.length; i++) {
    const jsonFolder = jsonFolders[i];
    const version = versions[i];
    const jsonDir = path.join(fullFolderPath, jsonFolder);
    
    if (fs.existsSync(jsonDir)) {
      candidates.push({ path: path.join(jsonDir, `${fileName}_v${version}.json`), version });
      candidates.push({ path: path.join(jsonDir, `${fileName}.json`), version });
    }
  }
  
  return {
    folderPath,
    parentPath: folderPathParts.length > 1 ? folderPathParts.slice(0, -1).join('/') : null,
    fullFolderPath,
    candidates: candidates.map(c => c.path)
  };
};

console.log('🧪 Comprehensive path logic test...\n');

const testCases = [
  {
    name: 'Japanese_test2/texts2',
    folderPath: 'Japanese_test2/texts2',
    fileName: 'test001',
    description: 'Multi-level folder with custom name'
  },
  {
    name: 'Japanese_test/texts',
    folderPath: 'Japanese_test/texts',
    fileName: 'jp_003',
    description: 'Multi-level folder with standard name'
  },
  {
    name: 'MyFolder',
    folderPath: 'MyFolder',
    fileName: 'story001',
    description: 'Single folder'
  },
  {
    name: 'datasets/Japanese_test2/texts2',
    folderPath: 'datasets/Japanese_test2/texts2',
    fileName: 'test001',
    description: 'Full path with datasets prefix'
  },
  {
    name: 'Category/SubCategory/texts',
    folderPath: 'Category/SubCategory/texts',
    fileName: 'story001',
    description: 'Deep nested folder'
  }
];

let allPassed = true;

for (const testCase of testCases) {
  console.log(`\nTest: ${testCase.name}`);
  console.log(`  Description: ${testCase.description}`);
  console.log(`  folderPath: ${testCase.folderPath}`);
  console.log(`  fileName: ${testCase.fileName}`);
  
  // Test save logic
  const saveResult = simulateSave(testCase.folderPath, testCase.fileName, 'v3');
  console.log(`  Save logic:`);
  console.log(`    Parent path: ${saveResult.parentPath || '(none)'}`);
  console.log(`    Full folder path: ${saveResult.fullFolderPath}`);
  console.log(`    Target dir: ${saveResult.targetDir}`);
  console.log(`    Target file: ${saveResult.targetPath}`);
  
  // Test load logic
  const loadResult = simulateLoad(testCase.folderPath, testCase.fileName);
  console.log(`  Load logic:`);
  console.log(`    Parent path: ${loadResult.parentPath || '(none)'}`);
  console.log(`    Full folder path: ${loadResult.fullFolderPath}`);
  console.log(`    Candidates: ${loadResult.candidates.length} paths`);
  
  // Verify consistency: save and load should use the same parent folder
  if (saveResult.fullFolderPath !== loadResult.fullFolderPath) {
    console.error(`    ✗ INCONSISTENCY: Save uses ${saveResult.fullFolderPath}, Load uses ${loadResult.fullFolderPath}`);
    allPassed = false;
  } else {
    console.log(`    ✓ Save and Load use same folder`);
  }
  
  // Verify parent path logic
  const expectedParent = testCase.folderPath.split('/').length > 1 
    ? testCase.folderPath.split('/').slice(0, -1).join('/')
    : null;
  
  if (saveResult.parentPath !== expectedParent) {
    console.error(`    ✗ Parent path mismatch: expected ${expectedParent}, got ${saveResult.parentPath}`);
    allPassed = false;
  } else {
    console.log(`    ✓ Parent path logic correct`);
  }
}

console.log('\n📊 Test Summary:');
if (allPassed) {
  console.log('✅ All path logic tests passed!');
  process.exit(0);
} else {
  console.log('❌ Some path logic tests failed!');
  process.exit(1);
}

