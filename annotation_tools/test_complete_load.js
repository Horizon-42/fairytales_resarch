#!/usr/bin/env node
/**
 * Complete test for load functionality
 * Tests all scenarios including texts folder selection
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

const findParentFolderForTextsFile = (searchDir, fileName) => {
  if (!fs.existsSync(searchDir)) return null;
  
  try {
    const entries = fs.readdirSync(searchDir, { withFileTypes: true });
    
    for (const entry of entries) {
      if (entry.isDirectory()) {
        if (entry.name.startsWith('.') || entry.name.startsWith('json')) continue;
        
        const textsDir = path.join(searchDir, entry.name, 'texts');
        const traditionalTextsDir = path.join(searchDir, entry.name, 'traditional_texts');
        
        if (fs.existsSync(textsDir)) {
          const txtFile = path.join(textsDir, `${fileName}.txt`);
          if (fs.existsSync(txtFile)) {
            return entry.name;
          }
        }
        
        if (fs.existsSync(traditionalTextsDir)) {
          const txtFile = path.join(traditionalTextsDir, `${fileName}.txt`);
          if (fs.existsSync(txtFile)) {
            return entry.name;
          }
        }
        
        const found = findParentFolderForTextsFile(path.join(searchDir, entry.name), fileName);
        if (found) {
          return path.join(entry.name, found);
        }
      }
    }
  } catch (err) {
    console.error(`Error searching: ${err.message}`);
  }
  
  return null;
};

console.log('🧪 Testing complete load functionality...\n');

// Test 1: originalPath with full path
console.log('Test 1: originalPath = "Japanese_test/texts/jp_003.txt"');
const path1 = 'Japanese_test/texts/jp_003.txt';
const parts1 = path1.split('/');
const fileName1 = path.basename(path1, path.extname(path1));
let baseFolderPath1 = parts1.slice(0, -1).join('/');
const lastPart1 = parts1.length >= 2 ? parts1[parts1.length - 2] : null;

if (lastPart1 === 'texts' || lastPart1 === 'traditional_texts') {
  if (parts1.length > 2) {
    baseFolderPath1 = parts1.slice(0, -2).join('/');
  } else {
    const datasetsDir = path.join(PROJECT_ROOT, 'datasets');
    baseFolderPath1 = findParentFolderForTextsFile(datasetsDir, fileName1);
  }
}

const fullPath1 = resolveFolderPath(baseFolderPath1);
const jsonPath1 = path.join(fullPath1, 'json_v3', `${fileName1}_v3.json`);
console.log(`  Base folder: ${baseFolderPath1}`);
console.log(`  Full folder path: ${fullPath1}`);
console.log(`  Expected JSON: ${jsonPath1}`);
console.log(`  File exists: ${fs.existsSync(jsonPath1) ? '✓' : '✗'}\n`);

// Test 2: originalPath with only texts/
console.log('Test 2: originalPath = "texts/jp_003.txt"');
const path2 = 'texts/jp_003.txt';
const parts2 = path2.split('/');
const fileName2 = path.basename(path2, path.extname(path2));
let baseFolderPath2 = parts2.slice(0, -1).join('/');
const lastPart2 = parts2.length >= 2 ? parts2[parts2.length - 2] : null;

if (lastPart2 === 'texts' || lastPart2 === 'traditional_texts') {
  if (parts2.length > 2) {
    baseFolderPath2 = parts2.slice(0, -2).join('/');
  } else {
    const datasetsDir = path.join(PROJECT_ROOT, 'datasets');
    baseFolderPath2 = findParentFolderForTextsFile(datasetsDir, fileName2);
  }
}

const fullPath2 = resolveFolderPath(baseFolderPath2);
const jsonPath2 = path.join(fullPath2, 'json_v3', `${fileName2}_v3.json`);
console.log(`  Base folder: ${baseFolderPath2}`);
console.log(`  Full folder path: ${fullPath2}`);
console.log(`  Expected JSON: ${jsonPath2}`);
console.log(`  File exists: ${fs.existsSync(jsonPath2) ? '✓' : '✗'}\n`);

// Test 3: folderPath + fileName
console.log('Test 3: folderPath = "Japanese_test", fileName = "jp_003"');
const folderPath3 = 'Japanese_test';
const fileName3 = 'jp_003';
const fullPath3 = resolveFolderPath(folderPath3);
const jsonPath3 = path.join(fullPath3, 'json_v3', `${fileName3}_v3.json`);
console.log(`  Full folder path: ${fullPath3}`);
console.log(`  Expected JSON: ${jsonPath3}`);
console.log(`  File exists: ${fs.existsSync(jsonPath3) ? '✓' : '✗'}\n`);

// Summary
const allPassed = fs.existsSync(jsonPath1) && fs.existsSync(jsonPath2) && fs.existsSync(jsonPath3);
console.log('📊 Test Summary:');
console.log(`  Test 1 (full path): ${fs.existsSync(jsonPath1) ? '✓ PASS' : '✗ FAIL'}`);
console.log(`  Test 2 (texts only): ${fs.existsSync(jsonPath2) ? '✓ PASS' : '✗ FAIL'}`);
console.log(`  Test 3 (folderPath): ${fs.existsSync(jsonPath3) ? '✓ PASS' : '✗ FAIL'}`);

if (allPassed) {
  console.log('\n✅ All tests passed!');
  process.exit(0);
} else {
  console.log('\n❌ Some tests failed!');
  process.exit(1);
}

