#!/usr/bin/env node
/**
 * Simple test for the new path logic
 * Tests: user selects texts folder, json folders created at same level
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

console.log('🧪 Testing simple path logic...\n');

// Test case 1: User selects "Japanese_test/texts" folder
console.log('Test 1: folderPath = "Japanese_test/texts"');
const folderPath1 = 'Japanese_test/texts';
const folderPathParts1 = folderPath1.split('/');
const lastPart1 = folderPathParts1[folderPathParts1.length - 1];

let fullPath1 = resolveFolderPath(folderPath1);
if (lastPart1 === 'texts') {
  if (folderPathParts1.length > 1) {
    const parentPath = folderPathParts1.slice(0, -1).join('/');
    fullPath1 = resolveFolderPath(parentPath);
  }
}

const jsonPath1 = path.join(fullPath1, 'json_v3', 'jp_003_v3.json');
console.log(`  Resolved folder: ${fullPath1}`);
console.log(`  JSON path: ${jsonPath1}`);
console.log(`  File exists: ${fs.existsSync(jsonPath1) ? '✓' : '✗'}\n`);

// Test case 2: User selects "Japanese_test" folder (not texts)
console.log('Test 2: folderPath = "Japanese_test"');
const folderPath2 = 'Japanese_test';
const folderPathParts2 = folderPath2.split('/');
const lastPart2 = folderPathParts2[folderPathParts2.length - 1];

let fullPath2 = resolveFolderPath(folderPath2);
if (lastPart2 === 'texts') {
  if (folderPathParts2.length > 1) {
    const parentPath = folderPathParts2.slice(0, -1).join('/');
    fullPath2 = resolveFolderPath(parentPath);
  }
}

const jsonPath2 = path.join(fullPath2, 'json_v3', 'jp_003_v3.json');
console.log(`  Resolved folder: ${fullPath2}`);
console.log(`  JSON path: ${jsonPath2}`);
console.log(`  File exists: ${fs.existsSync(jsonPath2) ? '✓' : '✗'}\n`);

// Test case 3: originalPath = "texts/jp_003.txt"
console.log('Test 3: originalPath = "texts/jp_003.txt"');
const originalPath3 = 'texts/jp_003.txt';
const pathParts3 = originalPath3.split('/');
const fileName3 = path.basename(originalPath3, path.extname(originalPath3));
let baseFolderPath3 = pathParts3.slice(0, -1).join('/');
const lastPart3 = pathParts3.length >= 2 ? pathParts3[pathParts3.length - 2] : null;

if (lastPart3 === 'texts') {
  if (pathParts3.length > 2) {
    baseFolderPath3 = pathParts3.slice(0, -2).join('/');
  }
}

const fullPath3 = resolveFolderPath(baseFolderPath3);
const jsonPath3 = path.join(fullPath3, 'json_v3', `${fileName3}_v3.json`);
console.log(`  Base folder: ${baseFolderPath3}`);
console.log(`  Resolved folder: ${fullPath3}`);
console.log(`  JSON path: ${jsonPath3}`);
console.log(`  File exists: ${fs.existsSync(jsonPath3) ? '✓' : '✗'}\n`);

// Summary
const allPassed = fs.existsSync(jsonPath1) && fs.existsSync(jsonPath2) && fs.existsSync(jsonPath3);
console.log('📊 Test Summary:');
console.log(`  Test 1 (texts folder): ${fs.existsSync(jsonPath1) ? '✓ PASS' : '✗ FAIL'}`);
console.log(`  Test 2 (parent folder): ${fs.existsSync(jsonPath2) ? '✓ PASS' : '✗ FAIL'}`);
console.log(`  Test 3 (originalPath): ${fs.existsSync(jsonPath3) ? '✓ PASS' : '✗ FAIL'}`);

if (allPassed) {
  console.log('\n✅ All tests passed!');
  process.exit(0);
} else {
  console.log('\n❌ Some tests failed!');
  process.exit(1);
}

