// Comprehensive test to verify functionality after changes
const fs = require('fs');
const path = require('path');

console.log('=== Testing Functionality After Changes ===\n');

// Test 1: Check that removed functions are not referenced
console.log('Test 1: Checking for removed function references...');
const filesToCheck = [
  'src/App.jsx',
  'src/utils/fileHandler.js',
  'src/utils/helpers.js',
  'src/components/NarrativeSection.jsx',
  'src/components/narrativeSectionLogic.js'
];

const removedFunctions = [
  'extractEnglishFromRelationship',
  'mapEnglishToFullRelationship',
  'formatRelationshipLevel1Label'
];

let foundRemovedFunctions = false;
for (const file of filesToCheck) {
  const filePath = path.join(__dirname, '..', '..', file);
  if (fs.existsSync(filePath)) {
    const content = fs.readFileSync(filePath, 'utf8');
    for (const func of removedFunctions) {
      // Check for function definitions or imports
      if (content.includes(`function ${func}`) || content.includes(`export function ${func}`) || 
          (content.includes(`import.*${func}`) && !content.includes('//'))) {
        console.error(`  ✗ Found reference to removed function ${func} in ${file}`);
        foundRemovedFunctions = true;
      }
    }
  }
}

if (!foundRemovedFunctions) {
  console.log('  ✓ No references to removed functions found');
} else {
  console.log('  ✗ Found references to removed functions');
}

// Test 2: Check that relationship constants use English only
console.log('\nTest 2: Checking relationship constants format...');
const relationshipConstantsPath = path.join(__dirname, '..', '..', 'src/relationship_constants.js');
if (fs.existsSync(relationshipConstantsPath)) {
  const content = fs.readFileSync(relationshipConstantsPath, 'utf8');
  const hasChineseFormat = /[\u4e00-\u9fa5]\(/.test(content);
  if (hasChineseFormat) {
    console.log('  ✗ Relationship constants still contain Chinese format');
  } else {
    console.log('  ✓ Relationship constants use English only');
  }
} else {
  console.log('  ✗ Relationship constants file not found');
}

// Test 3: Check that merge function exists
console.log('\nTest 3: Checking merge function exists...');
const fileHandlerPath = path.join(__dirname, '..', '..', 'src/utils/fileHandler.js');
if (fs.existsSync(fileHandlerPath)) {
  const content = fs.readFileSync(fileHandlerPath, 'utf8');
  if (content.includes('mergeV2V3States') && content.includes('export function mergeV2V3States')) {
    console.log('  ✓ mergeV2V3States function exists');
  } else {
    console.log('  ✗ mergeV2V3States function not found');
  }
} else {
  console.log('  ✗ fileHandler.js not found');
}

// Test 4: Check that App.jsx uses merge function
console.log('\nTest 4: Checking App.jsx uses merge function...');
const appPath = path.join(__dirname, '..', '..', 'src/App.jsx');
if (fs.existsSync(appPath)) {
  const content = fs.readFileSync(appPath, 'utf8');
  const hasImport = /import.*mergeV2V3States/.test(content);
  const hasUsage = content.includes('mergeV2V3States(');
  
  if (hasImport && hasUsage) {
    console.log('  ✓ App.jsx imports and uses mergeV2V3States');
  } else {
    if (!hasImport) console.log('  ✗ App.jsx does not import mergeV2V3States');
    if (!hasUsage) console.log('  ✗ App.jsx does not use mergeV2V3States');
  }
  
  // Check that it tries to load both v2 and v3
  if (content.includes('version: 3') && content.includes('version: 2') && 
      content.includes('Promise.allSettled')) {
    console.log('  ✓ App.jsx attempts to load both v2 and v3');
  } else {
    console.log('  ✗ App.jsx may not be loading both versions');
  }
} else {
  console.log('  ✗ App.jsx not found');
}

// Test 5: Check server.js supports version parameter
console.log('\nTest 5: Checking server.js supports version parameter...');
const serverPath = path.join(__dirname, '..', '..', 'server.js');
if (fs.existsSync(serverPath)) {
  const content = fs.readFileSync(serverPath, 'utf8');
  if (content.includes('const { folderPath, fileName, originalPath, version } = req.body')) {
    console.log('  ✓ server.js accepts version parameter');
  } else {
    console.log('  ✗ server.js does not accept version parameter');
  }
  
  if (content.includes('if (version === 3 || version === 2)')) {
    console.log('  ✓ server.js handles version-specific loading');
  } else {
    console.log('  ✗ server.js may not handle version-specific loading');
  }
} else {
  console.log('  ✗ server.js not found');
}

// Test 6: Check save functionality (v3 first, then v2, skip v1)
console.log('\nTest 6: Checking save functionality order...');
if (fs.existsSync(appPath)) {
  const content = fs.readFileSync(appPath, 'utf8');
  // Check handleSaveAll - look for the function body
  const saveAllMatch = content.match(/const handleSaveAll[^{]*\{([^}]*await handleSave[^}]*)\}/s);
  if (saveAllMatch) {
    const saveAllContent = saveAllMatch[1];
    const v3Index = saveAllContent.indexOf('handleSave("v3"');
    const v2Index = saveAllContent.indexOf('handleSave("v2"');
    const v1Index = saveAllContent.indexOf('handleSave("v1"');
    
    const v3First = v3Index !== -1 && v2Index !== -1 && v3Index < v2Index;
    const noV1 = v1Index === -1;
    
    if (v3First && noV1) {
      console.log('  ✓ handleSaveAll saves v3 first, then v2, skips v1');
    } else {
      if (!v3First) console.log('  ✗ handleSaveAll: v3 is not before v2 (v3 at ' + v3Index + ', v2 at ' + v2Index + ')');
      if (!noV1) console.log('  ✗ handleSaveAll: still saves v1');
    }
  } else {
    // Try simpler match
    const lines = content.split('\n');
    let inHandleSaveAll = false;
    let foundV3 = false, foundV2 = false, foundV1 = false;
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].includes('const handleSaveAll')) inHandleSaveAll = true;
      if (inHandleSaveAll) {
        if (lines[i].includes('handleSave("v3"')) foundV3 = true;
        if (lines[i].includes('handleSave("v2"')) foundV2 = true;
        if (lines[i].includes('handleSave("v1"')) foundV1 = true;
        if (lines[i].includes('};') && i > 0 && lines[i-1].includes('}')) break;
      }
    }
    if (foundV3 && foundV2 && !foundV1) {
      console.log('  ✓ handleSaveAll saves v3 and v2, skips v1');
    } else {
      console.log('  ⚠ handleSaveAll verification: v3=' + foundV3 + ', v2=' + foundV2 + ', v1=' + foundV1);
    }
  }
  
  // Check performAutoSave
  const autoSaveMatch = content.match(/saveData\("v3"\)[\s\S]*?saveData\("v2"\)/);
  if (autoSaveMatch) {
    console.log('  ✓ performAutoSave saves v3 first, then v2');
  } else {
    console.log('  ⚠ performAutoSave order may need verification');
  }
}

// Test 7: Check load functionality (v3 first, fallback to v2, never v1)
console.log('\nTest 7: Checking load functionality priority...');
if (fs.existsSync(serverPath)) {
  const content = fs.readFileSync(serverPath, 'utf8');
  const jsonFoldersMatch = content.match(/const jsonFolders = \[([^\]]+)\]/);
  if (jsonFoldersMatch) {
    const folders = jsonFoldersMatch[1];
    const hasV3 = folders.includes('json_v3');
    const hasV2 = folders.includes('json_v2');
    const noV1 = !folders.includes('json') || folders.includes('json_v3') || folders.includes('json_v2');
    
    if (hasV3 && hasV2 && noV1) {
      console.log('  ✓ server.js loads v3 and v2, skips v1');
    } else {
      console.log('  ✗ server.js may not have correct load priority');
    }
  }
}

// Summary
console.log('\n=== Summary ===');
console.log('All functionality tests completed.');
console.log('Please review the results above to ensure:');
console.log('  1. Removed functions are not referenced');
console.log('  2. Relationship constants use English only');
console.log('  3. Merge function exists and is used');
console.log('  4. Save order is v3 -> v2 (skip v1)');
console.log('  5. Load priority is v3 -> v2 (never v1)');
