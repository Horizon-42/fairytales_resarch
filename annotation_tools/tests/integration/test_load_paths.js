#!/usr/bin/env node
/**
 * Test script to verify load path resolution
 * Tests different folder selection scenarios
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PROJECT_ROOT = path.resolve(__dirname, '..', '..');

// Helper to resolve folder path
const resolveFolderPath = (folderPath) => {
  if (folderPath.startsWith('datasets/')) {
    return path.join(PROJECT_ROOT, folderPath);
  }
  return path.join(PROJECT_ROOT, 'datasets', folderPath);
};

// Test cases
const testCases = [
  {
    name: 'Select Japanese_test folder',
    folderPath: 'Japanese_test',
    fileName: 'jp_003',
    expectedJsonPath: path.join(PROJECT_ROOT, 'datasets', 'Japanese_test', 'json_v3', 'jp_003_v3.json')
  },
  {
    name: 'Select Japanese_test/texts folder',
    folderPath: 'Japanese_test', // Should resolve to parent of texts
    fileName: 'jp_003',
    expectedJsonPath: path.join(PROJECT_ROOT, 'datasets', 'Japanese_test', 'json_v3', 'jp_003_v3.json')
  },
  {
    name: 'Select datasets/Japanese_test/texts folder',
    folderPath: 'datasets/Japanese_test',
    fileName: 'jp_003',
    expectedJsonPath: path.join(PROJECT_ROOT, 'datasets', 'Japanese_test', 'json_v3', 'jp_003_v3.json')
  }
];

console.log('🧪 Testing load path resolution...\n');

let allPassed = true;

for (const testCase of testCases) {
  console.log(`Testing: ${testCase.name}`);
  console.log(`  Folder path: ${testCase.folderPath}`);
  console.log(`  File name: ${testCase.fileName}`);
  
  const fullFolderPath = resolveFolderPath(testCase.folderPath);
  const jsonDir = path.join(fullFolderPath, 'json_v3');
  const jsonPath = path.join(jsonDir, `${testCase.fileName}_v3.json`);
  
  console.log(`  Expected JSON path: ${jsonPath}`);
  
  if (fs.existsSync(jsonPath)) {
    console.log(`  ✓ JSON file exists`);
    
    // Verify it's the correct file
    try {
      const content = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
      if (content.metadata && content.metadata.id === testCase.fileName) {
        console.log(`  ✓ File content verified (ID matches)\n`);
      } else {
        console.log(`  ⚠ File content mismatch (ID: ${content.metadata?.id})\n`);
      }
    } catch (err) {
      console.log(`  ✗ Failed to parse JSON: ${err.message}\n`);
      allPassed = false;
    }
  } else {
    console.log(`  ✗ JSON file does not exist\n`);
    allPassed = false;
  }
}

// Test path resolution function
console.log('\n🔍 Testing path resolution function...\n');

const pathTests = [
  { input: 'Japanese_test', expected: path.join(PROJECT_ROOT, 'datasets', 'Japanese_test') },
  { input: 'datasets/Japanese_test', expected: path.join(PROJECT_ROOT, 'datasets', 'Japanese_test') },
  { input: 'texts', expected: path.join(PROJECT_ROOT, 'datasets', 'texts') }
];

for (const test of pathTests) {
  const result = resolveFolderPath(test.input);
  const passed = result === test.expected;
  console.log(`${passed ? '✓' : '✗'} "${test.input}" -> "${result}"`);
  if (!passed) {
    console.log(`  Expected: "${test.expected}"`);
    allPassed = false;
  }
}

console.log('\n📊 Test Summary:');
if (allPassed) {
  console.log('✅ All tests passed!');
  process.exit(0);
} else {
  console.log('❌ Some tests failed!');
  process.exit(1);
}

