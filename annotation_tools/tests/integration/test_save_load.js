#!/usr/bin/env node
/**
 * Test script for save/load functionality
 * Tests that files are saved and loaded correctly using folderPath and fileName
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PROJECT_ROOT = path.resolve(__dirname, '..', '..');

// Test configuration
const TEST_FOLDER = 'Japanese_test';
const TEST_FILE_NAME = 'jp_test_001';
const TEST_CONTENT = {
  version: "3.0",
  metadata: {
    id: TEST_FILE_NAME,
    title: "Test Story",
    culture: "Japanese",
    annotator: "test",
    date_annotated: "2025-01-01",
    confidence: 0.8
  },
  source_info: {
    language: "en",
    type: "summary",
    reference_uri: `datasets/${TEST_FOLDER}/texts/${TEST_FILE_NAME}.txt`,
    text_content: "This is a test story."
  },
  characters: [],
  narrative_events: [],
  themes_and_motifs: {
    ending_type: "HAPPY_ENDING",
    key_values: [],
    motif_type: [],
    atu_categories: [],
    obstacle_thrower: [],
    helper_type: [],
    thinking_process: "",
    atu_evidence: {},
    motif_evidence: {}
  },
  analysis: {
    propp_functions: [],
    propp_notes: "",
    paragraph_summaries: {
      per_section: {},
      combined: [],
      whole: ""
    },
    bias_reflection: {
      cultural_reading: "",
      gender_norms: "",
      hero_villain_mapping: "",
      ambiguous_motifs: []
    },
    qa_notes: ""
  }
};

// Helper functions
const resolveFolderPath = (folderPath) => {
  if (folderPath.startsWith('datasets/')) {
    return path.join(PROJECT_ROOT, folderPath);
  }
  return path.join(PROJECT_ROOT, 'datasets', folderPath);
};

const cleanup = () => {
  console.log('\n🧹 Cleaning up test files...');
  const testPaths = [
    path.join(resolveFolderPath(TEST_FOLDER), 'json_v3', `${TEST_FILE_NAME}_v3.json`),
    path.join(resolveFolderPath(TEST_FOLDER), 'json_v2', `${TEST_FILE_NAME}_v2.json`),
    path.join(resolveFolderPath(TEST_FOLDER), 'json', `${TEST_FILE_NAME}.json`)
  ];
  
  testPaths.forEach(testPath => {
    if (fs.existsSync(testPath)) {
      fs.unlinkSync(testPath);
      console.log(`  ✓ Deleted ${testPath}`);
    }
  });
};

// Test functions
const testSave = () => {
  console.log('\n📝 Testing save functionality...');
  
  const versions = ['v3', 'v2', 'v1'];
  let allPassed = true;
  
  for (const version of versions) {
    const targetDirName = version === 'v3' ? 'json_v3' : (version === 'v2' ? 'json_v2' : 'json');
    const fullFolderPath = resolveFolderPath(TEST_FOLDER);
    const targetDir = path.join(fullFolderPath, targetDirName);
    
    // Ensure directory exists
    fs.mkdirSync(targetDir, { recursive: true });
    
    // Create file
    const suffix = version === 'v3' ? '_v3' : (version === 'v2' ? '_v2' : '');
    const targetFileName = `${TEST_FILE_NAME}${suffix}.json`;
    const targetPath = path.join(targetDir, targetFileName);
    
    try {
      fs.writeFileSync(targetPath, JSON.stringify(TEST_CONTENT, null, 2));
      
      if (fs.existsSync(targetPath)) {
        console.log(`  ✓ Saved ${version}: ${targetPath}`);
      } else {
        console.error(`  ✗ Failed to save ${version}: File not found`);
        allPassed = false;
      }
    } catch (err) {
      console.error(`  ✗ Failed to save ${version}: ${err.message}`);
      allPassed = false;
    }
  }
  
  return allPassed;
};

const testLoad = () => {
  console.log('\n📖 Testing load functionality...');
  
  const fullFolderPath = resolveFolderPath(TEST_FOLDER);
  const jsonFolders = ['json_v3', 'json_v2', 'json'];
  const versions = [3, 2, 1];
  let allPassed = true;
  
  for (let i = 0; i < jsonFolders.length; i++) {
    const jsonFolder = jsonFolders[i];
    const version = versions[i];
    const jsonDir = path.join(fullFolderPath, jsonFolder);
    
    if (!fs.existsSync(jsonDir)) {
      console.log(`  ⚠ Skipping ${jsonFolder}: directory does not exist`);
      continue;
    }
    
    // Try with suffix first
    const candidates = [
      path.join(jsonDir, `${TEST_FILE_NAME}_v${version}.json`),
      path.join(jsonDir, `${TEST_FILE_NAME}.json`)
    ];
    
    let found = false;
    for (const candidate of candidates) {
      if (fs.existsSync(candidate)) {
        try {
          const content = JSON.parse(fs.readFileSync(candidate, 'utf8'));
          if (content.metadata && content.metadata.id === TEST_FILE_NAME) {
            console.log(`  ✓ Loaded v${version} from: ${candidate}`);
            found = true;
            break;
          }
        } catch (err) {
          console.error(`  ✗ Failed to parse ${candidate}: ${err.message}`);
        }
      }
    }
    
    if (!found) {
      console.log(`  ⚠ No valid file found for v${version} in ${jsonFolder}`);
    }
  }
  
  return allPassed;
};

const testPathResolution = () => {
  console.log('\n🔍 Testing path resolution...');
  
  const testCases = [
    { input: 'Japanese_test', expected: path.join(PROJECT_ROOT, 'datasets', 'Japanese_test') },
    { input: 'datasets/Japanese_test', expected: path.join(PROJECT_ROOT, 'datasets', 'Japanese_test') },
    { input: 'ChineseTales', expected: path.join(PROJECT_ROOT, 'datasets', 'ChineseTales') }
  ];
  
  let allPassed = true;
  
  for (const testCase of testCases) {
    const result = resolveFolderPath(testCase.input);
    if (result === testCase.expected) {
      console.log(`  ✓ "${testCase.input}" -> "${result}"`);
    } else {
      console.error(`  ✗ "${testCase.input}" -> "${result}" (expected: "${testCase.expected}")`);
      allPassed = false;
    }
  }
  
  return allPassed;
};

// Run tests
const runTests = async () => {
  console.log('🧪 Running save/load tests...');
  console.log(`Project root: ${PROJECT_ROOT}`);
  console.log(`Test folder: ${TEST_FOLDER}`);
  console.log(`Test file: ${TEST_FILE_NAME}`);
  
  try {
    // Cleanup first
    cleanup();
    
    // Run tests
    const pathTest = testPathResolution();
    const saveTest = testSave();
    const loadTest = testLoad();
    
    // Summary
    console.log('\n📊 Test Summary:');
    console.log(`  Path Resolution: ${pathTest ? '✓ PASS' : '✗ FAIL'}`);
    console.log(`  Save: ${saveTest ? '✓ PASS' : '✗ FAIL'}`);
    console.log(`  Load: ${loadTest ? '✓ PASS' : '✗ FAIL'}`);
    
    const allPassed = pathTest && saveTest && loadTest;
    
    if (allPassed) {
      console.log('\n✅ All tests passed!');
      process.exit(0);
    } else {
      console.log('\n❌ Some tests failed!');
      process.exit(1);
    }
  } catch (err) {
    console.error('\n💥 Test error:', err);
    process.exit(1);
  } finally {
    // Cleanup after tests
    cleanup();
  }
};

runTests();

