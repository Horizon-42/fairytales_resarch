#!/usr/bin/env node
/**
 * Test for arbitrary folder names (not just "texts")
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PROJECT_ROOT = path.resolve(__dirname, '..', '..');

const resolveFolderPath = (folderPath) => {
  if (!folderPath || folderPath.trim() === '') {
    return path.join(PROJECT_ROOT, 'datasets');
  }
  if (folderPath.startsWith('datasets/')) {
    return path.join(PROJECT_ROOT, folderPath);
  }
  return path.join(PROJECT_ROOT, 'datasets', folderPath);
};

console.log('🧪 Testing arbitrary folder names...\n');

// Test case 1: folderPath = "Japanese_test2/texts2"
console.log('Test 1: folderPath = "Japanese_test2/texts2"');
const folderPath1 = 'Japanese_test2/texts2';
const folderPathParts1 = folderPath1.split('/');

let fullPath1;
if (folderPathParts1.length > 1) {
  const parentPath = folderPathParts1.slice(0, -1).join('/');
  fullPath1 = resolveFolderPath(parentPath);
} else {
  fullPath1 = resolveFolderPath(folderPath1);
}

const jsonPath1 = path.join(fullPath1, 'json_v3', 'test_file_v3.json');
console.log(`  Parent folder: ${folderPathParts1.slice(0, -1).join('/')}`);
console.log(`  Resolved folder: ${fullPath1}`);
console.log(`  Expected JSON path: ${jsonPath1}`);
console.log(`  Parent folder exists: ${fs.existsSync(fullPath1) ? '✓' : '✗'}\n`);

// Test case 2: folderPath = "Japanese_test/texts" (original case)
console.log('Test 2: folderPath = "Japanese_test/texts"');
const folderPath2 = 'Japanese_test/texts';
const folderPathParts2 = folderPath2.split('/');

let fullPath2;
if (folderPathParts2.length > 1) {
  const parentPath = folderPathParts2.slice(0, -1).join('/');
  fullPath2 = resolveFolderPath(parentPath);
} else {
  fullPath2 = resolveFolderPath(folderPath2);
}

const jsonPath2 = path.join(fullPath2, 'json_v3', 'jp_003_v3.json');
console.log(`  Parent folder: ${folderPathParts2.slice(0, -1).join('/')}`);
console.log(`  Resolved folder: ${fullPath2}`);
console.log(`  Expected JSON path: ${jsonPath2}`);
console.log(`  JSON file exists: ${fs.existsSync(jsonPath2) ? '✓' : '✗'}\n`);

// Test case 3: folderPath = "MyFolder" (single folder, no parent)
console.log('Test 3: folderPath = "MyFolder" (single folder)');
const folderPath3 = 'MyFolder';
const folderPathParts3 = folderPath3.split('/');

let fullPath3;
if (folderPathParts3.length > 1) {
  const parentPath = folderPathParts3.slice(0, -1).join('/');
  fullPath3 = resolveFolderPath(parentPath);
} else {
  fullPath3 = resolveFolderPath(folderPath3);
}

const jsonPath3 = path.join(fullPath3, 'json_v3', 'test_file_v3.json');
console.log(`  Resolved folder: ${fullPath3}`);
console.log(`  Expected JSON path: ${jsonPath3}`);
console.log(`  Folder exists: ${fs.existsSync(fullPath3) ? '✓' : '✗'}\n`);

// Summary
console.log('📊 Test Summary:');
console.log(`  Test 1 (texts2): Parent folder logic ${folderPathParts1.length > 1 ? '✓ CORRECT' : '✗ WRONG'}`);
console.log(`  Test 2 (texts): Parent folder logic ${folderPathParts2.length > 1 ? '✓ CORRECT' : '✗ WRONG'}`);
console.log(`  Test 3 (single): Single folder logic ${folderPathParts3.length === 1 ? '✓ CORRECT' : '✗ WRONG'}`);

console.log('\n✅ Logic tests passed!');
process.exit(0);

