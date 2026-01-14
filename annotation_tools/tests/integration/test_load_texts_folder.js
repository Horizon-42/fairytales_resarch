#!/usr/bin/env node
/**
 * Test script to verify loading when texts folder is selected
 * Simulates the scenario: user selects datasets/Japanese_test/texts folder
 */

import http from 'http';

const API_BASE = 'http://localhost:3001';
const TEST_FILE_NAME = 'jp_003';

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

// Test cases
const testCases = [
  {
    name: 'Load with originalPath: texts/jp_003.txt',
    request: { originalPath: 'texts/jp_003.txt' },
    expectedFolder: 'Japanese_test'
  },
  {
    name: 'Load with originalPath: Japanese_test/texts/jp_003.txt',
    request: { originalPath: 'Japanese_test/texts/jp_003.txt' },
    expectedFolder: 'Japanese_test'
  },
  {
    name: 'Load with folderPath and fileName',
    request: { folderPath: 'Japanese_test', fileName: TEST_FILE_NAME },
    expectedFolder: 'Japanese_test'
  }
];

const runTests = async () => {
  console.log('🧪 Testing load API with texts folder selection...\n');
  console.log(`API Base: ${API_BASE}`);
  console.log(`Test file: ${TEST_FILE_NAME}\n`);
  
  // Check if server is running
  try {
    await makeRequest('OPTIONS', '/api/save');
    console.log('✓ Server is running\n');
  } catch (err) {
    console.error('✗ Server is not running. Please start the server first:');
    console.error('  cd annotation_tools && npm run server');
    process.exit(1);
  }
  
  let allPassed = true;
  
  for (const testCase of testCases) {
    console.log(`Testing: ${testCase.name}`);
    console.log(`  Request:`, JSON.stringify(testCase.request));
    
    try {
      const response = await makeRequest('POST', '/api/load', testCase.request);
      
      if (response.status === 200 && response.data.found) {
        console.log(`  ✓ Load successful: v${response.data.version}`);
        console.log(`    Path: ${response.data.path}`);
        
        // Verify the path contains the expected folder
        if (response.data.path.includes(testCase.expectedFolder)) {
          console.log(`    ✓ Path contains expected folder: ${testCase.expectedFolder}`);
        } else {
          console.error(`    ✗ Path does not contain expected folder: ${testCase.expectedFolder}`);
          allPassed = false;
        }
        
        // Verify content
        if (response.data.content.metadata && response.data.content.metadata.id === TEST_FILE_NAME) {
          console.log(`    ✓ Content verified: ID matches\n`);
        } else {
          console.error(`    ✗ Content mismatch: expected ${TEST_FILE_NAME}, got ${response.data.content.metadata?.id}\n`);
          allPassed = false;
        }
      } else {
        console.error(`  ✗ Load failed:`, response.data);
        allPassed = false;
      }
    } catch (err) {
      console.error(`  ✗ Load error:`, err.message);
      allPassed = false;
    }
  }
  
  console.log('\n📊 Test Summary:');
  if (allPassed) {
    console.log('✅ All load tests passed!');
    process.exit(0);
  } else {
    console.log('❌ Some load tests failed!');
    process.exit(1);
  }
};

runTests();

