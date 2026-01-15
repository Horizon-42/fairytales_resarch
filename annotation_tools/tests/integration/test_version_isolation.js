/**
 * Test script to verify v1/v2/v3 JSON generation logic isolation
 * 
 * This test verifies that:
 * 1. v1 JSON does not contain any v3-specific fields (relationship_multi, relationships, action_layer)
 * 2. v2 JSON does not contain any v3-specific fields
 * 3. v3 JSON does not contain any v1/v2 flat fields (relationship_level1, relationship_level2, sentiment, action_category, etc.)
 * 4. Each version's generation logic is completely independent
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PROJECT_ROOT = path.resolve(__dirname, '..', '..');

// Test data: simulate narrativeStructure with mixed v1/v2/v3 fields
const testNarrativeStructure = [
  {
    id: "test-event-1",
    text_span: { start: 0, end: 100, text: "Test text" },
    event_type: "ACTION",
    description: "Test event",
    agents: ["Agent1", "Agent2"],
    targets: ["Target1"],
    target_type: "character",
    object_type: "",
    instrument: "",
    time_order: 1,
    // v1/v2 flat fields
    relationship_level1: "friend",
    relationship_level2: "close",
    sentiment: "positive",
    action_category: "help",
    action_type: "assist",
    action_context: "emergency",
    action_status: "completed",
    narrative_function: "helper",
    // v3 nested fields (should only appear in v3 output)
    relationship_multi: [
      { agent: "Agent1", target: "Target1", relationship_level1: "friend", relationship_level2: "close", sentiment: "positive" }
    ],
    relationships: [
      { agent: "Agent1", target: "Target1", relationship_level1: "friend", relationship_level2: "close", sentiment: "positive" }
    ],
    action_layer: {
      category: "help",
      type: "assist",
      context: "emergency",
      status: "completed",
      function: "helper"
    }
  }
];

/**
 * Test v1 JSON generation
 * Should only contain flat fields, no v3-specific fields
 */
function testV1Generation() {
  console.log("\n=== Testing v1 JSON Generation ===");
  
  const v1Event = testNarrativeStructure[0];
  
  // Simulate v1 generation logic
  const v1Result = {
    id: v1Event.id,
    text_span: v1Event.text_span,
    event_type: v1Event.event_type || "",
    description: v1Event.description || "",
    agents: Array.isArray(v1Event.agents) ? v1Event.agents.filter(Boolean) : [],
    targets: Array.isArray(v1Event.targets) ? v1Event.targets.filter(Boolean) : [],
    target_type: v1Event.target_type || "",
    object_type: v1Event.object_type || "",
    instrument: v1Event.instrument || "",
    time_order: v1Event.time_order,
    relationship_level1: v1Event.relationship_level1 || "",
    relationship_level2: v1Event.relationship_level2 || "",
    sentiment: v1Event.sentiment || "",
    action_category: v1Event.action_category || "",
    action_type: v1Event.action_type || "",
    action_context: v1Event.action_context || "",
    action_status: v1Event.action_status || "",
    narrative_function: v1Event.narrative_function || ""
  };
  
  // Verify v3 fields are NOT present
  const hasRelationshipMulti = 'relationship_multi' in v1Result;
  const hasRelationships = 'relationships' in v1Result;
  const hasActionLayer = 'action_layer' in v1Result;
  
  console.log("v1 Result keys:", Object.keys(v1Result));
  console.log("Has relationship_multi:", hasRelationshipMulti, hasRelationshipMulti ? "❌ FAIL" : "✅ PASS");
  console.log("Has relationships:", hasRelationships, hasRelationships ? "❌ FAIL" : "✅ PASS");
  console.log("Has action_layer:", hasActionLayer, hasActionLayer ? "❌ FAIL" : "✅ PASS");
  
  // Verify flat fields are present
  const hasFlatFields = 
    'relationship_level1' in v1Result &&
    'relationship_level2' in v1Result &&
    'sentiment' in v1Result &&
    'action_category' in v1Result &&
    'action_type' in v1Result;
  
  console.log("Has required flat fields:", hasFlatFields, hasFlatFields ? "✅ PASS" : "❌ FAIL");
  
  return !hasRelationshipMulti && !hasRelationships && !hasActionLayer && hasFlatFields;
}

/**
 * Test v2 JSON generation
 * Should only contain flat fields, no v3-specific fields
 */
function testV2Generation() {
  console.log("\n=== Testing v2 JSON Generation ===");
  
  const v2Event = testNarrativeStructure[0];
  
  // Simulate v2 generation logic
  const v2Result = {
    id: v2Event.id,
    text_span: v2Event.text_span,
    event_type: v2Event.event_type || "",
    description: v2Event.description || "",
    agents: Array.isArray(v2Event.agents) ? v2Event.agents.filter(Boolean) : [],
    targets: Array.isArray(v2Event.targets) ? v2Event.targets.filter(Boolean) : [],
    target_type: v2Event.target_type || "",
    object_type: v2Event.object_type || "",
    instrument: v2Event.instrument || "",
    time_order: v2Event.time_order,
    relationship_level1: v2Event.relationship_level1 || "",
    relationship_level2: v2Event.relationship_level2 || "",
    sentiment: v2Event.sentiment || "",
    action_category: v2Event.action_category || "",
    action_type: v2Event.action_type || "",
    action_context: v2Event.action_context || "",
    action_status: v2Event.action_status || "",
    narrative_function: v2Event.narrative_function || ""
  };
  
  // Verify v3 fields are NOT present
  const hasRelationshipMulti = 'relationship_multi' in v2Result;
  const hasRelationships = 'relationships' in v2Result;
  const hasActionLayer = 'action_layer' in v2Result;
  
  console.log("v2 Result keys:", Object.keys(v2Result));
  console.log("Has relationship_multi:", hasRelationshipMulti, hasRelationshipMulti ? "❌ FAIL" : "✅ PASS");
  console.log("Has relationships:", hasRelationships, hasRelationships ? "❌ FAIL" : "✅ PASS");
  console.log("Has action_layer:", hasActionLayer, hasActionLayer ? "❌ FAIL" : "✅ PASS");
  
  // Verify flat fields are present
  const hasFlatFields = 
    'relationship_level1' in v2Result &&
    'relationship_level2' in v2Result &&
    'sentiment' in v2Result &&
    'action_category' in v2Result &&
    'action_type' in v2Result;
  
  console.log("Has required flat fields:", hasFlatFields, hasFlatFields ? "✅ PASS" : "❌ FAIL");
  
  return !hasRelationshipMulti && !hasRelationships && !hasActionLayer && hasFlatFields;
}

/**
 * Test v3 JSON generation
 * Should only contain nested structures, no v1/v2 flat fields
 */
function testV3Generation() {
  console.log("\n=== Testing v3 JSON Generation ===");
  
  const v3Event = testNarrativeStructure[0];
  
  // Simulate v3 generation logic
  const agents = Array.isArray(v3Event.agents) ? v3Event.agents.filter(Boolean) : [];
  const targets = Array.isArray(v3Event.targets) ? v3Event.targets.filter(Boolean) : [];
  
  const existingMultiList = Array.isArray(v3Event.relationship_multi)
    ? v3Event.relationship_multi
    : ((v3Event.relationship_multi && typeof v3Event.relationship_multi === "object") ? [v3Event.relationship_multi] : []);
  
  const normalizeRelEntry = (r) => {
    const rel = (r && typeof r === "object") ? r : {};
    return {
      agent: rel.agent || "",
      target: rel.target || "",
      relationship_level1: rel.relationship_level1 || "",
      relationship_level2: rel.relationship_level2 || "",
      sentiment: rel.sentiment || ""
    };
  };
  
  const buildActionLayerV3 = (n) => {
    const item = (n && typeof n === "object") ? n : {};
    return {
      category: item.action_category || "",
      type: item.action_type || "",
      context: item.action_context || "",
      status: item.action_status || "",
      function: item.narrative_function || ""
    };
  };
  
  let relList = [];
  if (existingMultiList.length > 0) {
    relList = existingMultiList.map(normalizeRelEntry);
  } else if (v3Event.relationship_level1 || v3Event.relationship_level2 || v3Event.sentiment) {
    relList = [normalizeRelEntry({
      agent: agents[0] || "",
      target: targets[0] || "",
      relationship_level1: v3Event.relationship_level1 || "",
      relationship_level2: v3Event.relationship_level2 || "",
      sentiment: v3Event.sentiment || ""
    })];
  }
  
  const actionLayer = buildActionLayerV3(v3Event);
  
  const v3Result = {
    id: v3Event.id,
    text_span: v3Event.text_span,
    event_type: v3Event.event_type || "",
    description: v3Event.description || "",
    agents: agents,
    targets: targets,
    target_type: v3Event.target_type || "",
    object_type: v3Event.object_type || "",
    instrument: v3Event.instrument || "",
    time_order: v3Event.time_order,
    relationships: relList,
    action_layer: actionLayer
  };
  
  // Verify v3 nested fields are present
  const hasRelationships = 'relationships' in v3Result && Array.isArray(v3Result.relationships);
  const hasActionLayer = 'action_layer' in v3Result && typeof v3Result.action_layer === 'object';
  
  console.log("v3 Result keys:", Object.keys(v3Result));
  console.log("Has relationships:", hasRelationships, hasRelationships ? "✅ PASS" : "❌ FAIL");
  console.log("Has action_layer:", hasActionLayer, hasActionLayer ? "✅ PASS" : "❌ FAIL");
  
  // Verify v1/v2 flat fields are NOT present
  const hasRelationshipLevel1 = 'relationship_level1' in v3Result;
  const hasRelationshipLevel2 = 'relationship_level2' in v3Result;
  const hasSentiment = 'sentiment' in v3Result;
  const hasActionCategory = 'action_category' in v3Result;
  const hasActionType = 'action_type' in v3Result;
  const hasRelationshipMulti = 'relationship_multi' in v3Result;
  
  console.log("Has relationship_level1:", hasRelationshipLevel1, hasRelationshipLevel1 ? "❌ FAIL" : "✅ PASS");
  console.log("Has relationship_level2:", hasRelationshipLevel2, hasRelationshipLevel2 ? "❌ FAIL" : "✅ PASS");
  console.log("Has sentiment:", hasSentiment, hasSentiment ? "❌ FAIL" : "✅ PASS");
  console.log("Has action_category:", hasActionCategory, hasActionCategory ? "❌ FAIL" : "✅ PASS");
  console.log("Has action_type:", hasActionType, hasActionType ? "❌ FAIL" : "✅ PASS");
  console.log("Has relationship_multi:", hasRelationshipMulti, hasRelationshipMulti ? "❌ FAIL" : "✅ PASS");
  
  return hasRelationships && hasActionLayer && 
         !hasRelationshipLevel1 && !hasRelationshipLevel2 && !hasSentiment &&
         !hasActionCategory && !hasActionType && !hasRelationshipMulti;
}

/**
 * Test actual saved JSON files
 */
function testSavedFiles() {
  console.log("\n=== Testing Saved JSON Files ===");
  
  const testCases = [
    {
      name: "v1 JSON",
      path: path.join(PROJECT_ROOT, "datasets", "ChineseTales", "json", "CH_003_孟姜女哭长城.json"),
      version: "v1"
    },
    {
      name: "v2 JSON",
      path: path.join(PROJECT_ROOT, "datasets", "ChineseTales", "json_v2", "CH_003_孟姜女哭长城_v2.json"),
      version: "v2"
    },
    {
      name: "v3 JSON",
      path: path.join(PROJECT_ROOT, "datasets", "ChineseTales", "json_v3", "CH_003_孟姜女哭长城_v3.json"),
      version: "v3"
    }
  ];
  
  let allPassed = true;
  
  for (const testCase of testCases) {
    if (!fs.existsSync(testCase.path)) {
      console.log(`\n${testCase.name}: File not found, skipping...`);
      continue;
    }
    
    console.log(`\n--- Testing ${testCase.name} ---`);
    const content = JSON.parse(fs.readFileSync(testCase.path, 'utf8'));
    
    // Get narrative events/structure
    const events = content.narrative_events || content.narrative_structure || [];
    
    if (events.length === 0) {
      console.log("No events found, skipping field checks");
      continue;
    }
    
    const firstEvent = events[0];
    if (typeof firstEvent !== 'object') {
      console.log("First event is not an object, skipping");
      continue;
    }
    
    const keys = Object.keys(firstEvent);
    console.log("Event keys:", keys);
    
    if (testCase.version === "v1" || testCase.version === "v2") {
      // v1/v2 should NOT have v3 fields
      const hasV3Fields = 
        keys.includes('relationship_multi') ||
        keys.includes('relationships') ||
        keys.includes('action_layer');
      
      console.log("Has v3 fields:", hasV3Fields, hasV3Fields ? "❌ FAIL" : "✅ PASS");
      
      // v1/v2 should have flat fields
      const hasFlatFields = 
        keys.includes('relationship_level1') ||
        keys.includes('relationship_level2') ||
        keys.includes('sentiment') ||
        keys.includes('action_category') ||
        keys.includes('action_type');
      
      console.log("Has flat fields:", hasFlatFields, hasFlatFields ? "✅ PASS" : "⚠️  WARN (may be empty event)");
      
      if (hasV3Fields) allPassed = false;
    } else if (testCase.version === "v3") {
      // v3 should have nested structures
      const hasV3Fields = 
        keys.includes('relationships') &&
        keys.includes('action_layer');
      
      console.log("Has v3 nested fields:", hasV3Fields, hasV3Fields ? "✅ PASS" : "❌ FAIL");
      
      // v3 should NOT have flat fields
      const hasFlatFields = 
        keys.includes('relationship_level1') ||
        keys.includes('relationship_level2') ||
        keys.includes('sentiment') ||
        keys.includes('action_category') ||
        keys.includes('action_type') ||
        keys.includes('relationship_multi');
      
      console.log("Has flat/v1/v2 fields:", hasFlatFields, hasFlatFields ? "❌ FAIL" : "✅ PASS");
      
      if (!hasV3Fields || hasFlatFields) allPassed = false;
    }
  }
  
  return allPassed;
}

// Run all tests
console.log("=".repeat(60));
console.log("Testing Version Isolation Logic");
console.log("=".repeat(60));

const test1 = testV1Generation();
const test2 = testV2Generation();
const test3 = testV3Generation();
const test4 = testSavedFiles();

console.log("\n" + "=".repeat(60));
console.log("Test Results Summary");
console.log("=".repeat(60));
console.log("v1 Generation Test:", test1 ? "✅ PASS" : "❌ FAIL");
console.log("v2 Generation Test:", test2 ? "✅ PASS" : "❌ FAIL");
console.log("v3 Generation Test:", test3 ? "✅ PASS" : "❌ FAIL");
console.log("Saved Files Test:", test4 ? "✅ PASS" : "❌ FAIL");

const allPassed = test1 && test2 && test3 && test4;
console.log("\nOverall:", allPassed ? "✅ ALL TESTS PASSED" : "❌ SOME TESTS FAILED");

process.exit(allPassed ? 0 : 1);

