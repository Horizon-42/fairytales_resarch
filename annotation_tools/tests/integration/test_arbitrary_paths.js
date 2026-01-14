#!/usr/bin/env node
/**
 * Test for arbitrary path resolution
 */

import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PROJECT_ROOT = path.resolve(__dirname, '..', '..');

// Simulate the new resolveFolderPath logic
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

console.log('🧪 Testing arbitrary path resolution...\n');
console.log(`Project root: ${PROJECT_ROOT}\n`);

const testCases = [
  {
    name: 'Relative path: Japanese_test2/texts2',
    input: 'Japanese_test2/texts2',
    expected: path.join(PROJECT_ROOT, 'Japanese_test2', 'texts2')
  },
  {
    name: 'Relative path with datasets/: datasets/Japanese_test2/texts2',
    input: 'datasets/Japanese_test2/texts2',
    expected: path.join(PROJECT_ROOT, 'datasets', 'Japanese_test2', 'texts2')
  },
  {
    name: 'Absolute path',
    input: '/home/user/my_folder/texts',
    expected: '/home/user/my_folder/texts'
  },
  {
    name: 'Empty path',
    input: '',
    expected: PROJECT_ROOT
  },
  {
    name: 'Single folder: MyFolder',
    input: 'MyFolder',
    expected: path.join(PROJECT_ROOT, 'MyFolder')
  }
];

let allPassed = true;

for (const testCase of testCases) {
  const result = resolveFolderPath(testCase.input);
  const passed = result === testCase.expected;
  
  console.log(`Test: ${testCase.name}`);
  console.log(`  Input: ${testCase.input}`);
  console.log(`  Expected: ${testCase.expected}`);
  console.log(`  Got: ${result}`);
  console.log(`  ${passed ? '✓ PASS' : '✗ FAIL'}\n`);
  
  if (!passed) {
    allPassed = false;
  }
}

// Test parent folder logic
console.log('\nTesting parent folder logic:\n');

const testParentCases = [
  {
    name: 'Multi-level: Japanese_test2/texts2',
    folderPath: 'Japanese_test2/texts2',
    expectedParent: 'Japanese_test2',
    expectedFullParent: path.join(PROJECT_ROOT, 'Japanese_test2')
  },
  {
    name: 'Multi-level with datasets: datasets/Japanese_test2/texts2',
    folderPath: 'datasets/Japanese_test2/texts2',
    expectedParent: 'datasets/Japanese_test2',
    expectedFullParent: path.join(PROJECT_ROOT, 'datasets', 'Japanese_test2')
  },
  {
    name: 'Absolute path: /home/user/my_folder/texts',
    folderPath: '/home/user/my_folder/texts',
    expectedParent: '/home/user/my_folder',
    expectedFullParent: '/home/user/my_folder'
  }
];

for (const testCase of testParentCases) {
  const folderPathParts = testCase.folderPath.split('/');
  let parentPath;
  
  if (folderPathParts.length > 1) {
    parentPath = folderPathParts.slice(0, -1).join('/');
  } else {
    parentPath = testCase.folderPath;
  }
  
  const fullParentPath = resolveFolderPath(parentPath);
  
  const passed = fullParentPath === testCase.expectedFullParent;
  
  console.log(`Test: ${testCase.name}`);
  console.log(`  folderPath: ${testCase.folderPath}`);
  console.log(`  Parent path: ${parentPath}`);
  console.log(`  Expected full parent: ${testCase.expectedFullParent}`);
  console.log(`  Got: ${fullParentPath}`);
  console.log(`  ${passed ? '✓ PASS' : '✗ FAIL'}\n`);
  
  if (!passed) {
    allPassed = false;
  }
}

console.log('\n📊 Test Summary:');
if (allPassed) {
  console.log('✅ All path resolution tests passed!');
  process.exit(0);
} else {
  console.log('❌ Some path resolution tests failed!');
  process.exit(1);
}

