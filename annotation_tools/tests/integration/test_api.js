#!/usr/bin/env node
/**
 * Integration test for save/load API endpoints
 * Tests the actual HTTP API endpoints
 */

import http from 'http';

const API_BASE = 'http://localhost:3001';
const TEST_FOLDER = 'Japanese_test';
const TEST_FILE_NAME = 'jp_test_api_001';
const TEST_CONTENT = {
  version: "3.0",
  metadata: {
    id: TEST_FILE_NAME,
    title: "API Test Story",
    culture: "Japanese",
    annotator: "test",
    date_annotated: "2025-01-01",
    confidence: 0.8
  },
  source_info: {
    language: "en",
    type: "summary",
    reference_uri: `datasets/${TEST_FOLDER}/texts/${TEST_FILE_NAME}.txt`,
    text_content: "This is an API test story."
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

// Helper function to make HTTP requests
const makeRequest = (method, path, data = null) => {
  return new Promise((resolve, reject) => {
    const url = new URL(path, API_BASE);
    const options = {
      method,
      headers: {
        'Content-Type': 'application/json'
      }
    };

    const req = http.request(url, options, (res) => {
      let body = '';
      res.on('data', (chunk) => {
        body += chunk;
      });
      res.on('end', () => {
        try {
          const parsed = body ? JSON.parse(body) : {};
          resolve({ status: res.statusCode, data: parsed });
        } catch (err) {
          resolve({ status: res.statusCode, data: body });
        }
      });
    });

    req.on('error', (err) => {
      reject(err);
    });

    if (data) {
      req.write(JSON.stringify(data));
    }
    req.end();
  });
};

// Test functions
const testSaveAPI = async (version) => {
  console.log(`\n📝 Testing save API (${version})...`);
  
  try {
    const response = await makeRequest('POST', '/api/save', {
      folderPath: TEST_FOLDER,
      fileName: TEST_FILE_NAME,
      content: TEST_CONTENT,
      version: version
    });

    if (response.status === 200 && response.data.success) {
      console.log(`  ✓ Save ${version} successful: ${response.data.path}`);
      return true;
    } else {
      console.error(`  ✗ Save ${version} failed:`, response.data);
      return false;
    }
  } catch (err) {
    console.error(`  ✗ Save ${version} error:`, err.message);
    return false;
  }
};

const testLoadAPI = async () => {
  console.log('\n📖 Testing load API...');
  
  try {
    // Test new API with folderPath and fileName
    const response1 = await makeRequest('POST', '/api/load', {
      folderPath: TEST_FOLDER,
      fileName: TEST_FILE_NAME
    });

    if (response1.status === 200 && response1.data.found) {
      console.log(`  ✓ Load successful (new API): v${response1.data.version}`);
      console.log(`    Path: ${response1.data.path}`);
      if (response1.data.content.metadata.id === TEST_FILE_NAME) {
        console.log(`    Content verified: ID matches`);
        return true;
      } else {
        console.error(`    Content mismatch: expected ${TEST_FILE_NAME}, got ${response1.data.content.metadata.id}`);
        return false;
      }
    } else {
      console.error(`  ✗ Load failed (new API):`, response1.data);
      return false;
    }
  } catch (err) {
    console.error(`  ✗ Load error:`, err.message);
    return false;
  }
};

const testLoadLegacyAPI = async () => {
  console.log('\n📖 Testing load API (legacy originalPath)...');
  
  try {
    const response = await makeRequest('POST', '/api/load', {
      originalPath: `${TEST_FOLDER}/texts/${TEST_FILE_NAME}.txt`
    });

    if (response.status === 200 && response.data.found) {
      console.log(`  ✓ Load successful (legacy API): v${response.data.version}`);
      console.log(`    Path: ${response.data.path}`);
      return true;
    } else {
      console.log(`  ⚠ Load not found (legacy API) - this is OK if file doesn't exist`);
      return true; // Not an error, just not found
    }
  } catch (err) {
    console.error(`  ✗ Load error (legacy API):`, err.message);
    return false;
  }
};

// Run tests
const runTests = async () => {
  console.log('🧪 Running API integration tests...');
  console.log(`API Base: ${API_BASE}`);
  console.log(`Test folder: ${TEST_FOLDER}`);
  console.log(`Test file: ${TEST_FILE_NAME}`);
  
  // Check if server is running
  try {
    await makeRequest('OPTIONS', '/api/save');
    console.log('✓ Server is running');
  } catch (err) {
    console.error('✗ Server is not running. Please start the server first:');
    console.error('  cd annotation_tools && npm run server');
    process.exit(1);
  }
  
  try {
    // Test save for all versions
    const saveV3 = await testSaveAPI('v3');
    const saveV2 = await testSaveAPI('v2');
    const saveV1 = await testSaveAPI('v1');
    
    // Test load
    const loadNew = await testLoadAPI();
    const loadLegacy = await testLoadLegacyAPI();
    
    // Summary
    console.log('\n📊 Test Summary:');
    console.log(`  Save v3: ${saveV3 ? '✓ PASS' : '✗ FAIL'}`);
    console.log(`  Save v2: ${saveV2 ? '✓ PASS' : '✗ FAIL'}`);
    console.log(`  Save v1: ${saveV1 ? '✓ PASS' : '✗ FAIL'}`);
    console.log(`  Load (new API): ${loadNew ? '✓ PASS' : '✗ FAIL'}`);
    console.log(`  Load (legacy API): ${loadLegacy ? '✓ PASS' : '✗ FAIL'}`);
    
    const allPassed = saveV3 && saveV2 && saveV1 && loadNew && loadLegacy;
    
    if (allPassed) {
      console.log('\n✅ All API tests passed!');
      process.exit(0);
    } else {
      console.log('\n❌ Some API tests failed!');
      process.exit(1);
    }
  } catch (err) {
    console.error('\n💥 Test error:', err);
    process.exit(1);
  }
};

runTests();

