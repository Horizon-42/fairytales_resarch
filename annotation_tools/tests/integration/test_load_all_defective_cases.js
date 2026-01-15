// Comprehensive test for loading various defective v3 JSON cases
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { mapV3ToState } from '../../src/utils/fileHandler.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PROJECT_ROOT = path.resolve(__dirname, '..', '..');

console.log('=== Comprehensive Defective V3 JSON Loading Test ===\n');

const testCases = [
  {
    name: "null agents/targets",
    json: {
      version: "3.0",
      metadata: { id: "test", title: "Test", culture: "Test" },
      source_info: { language: "en", type: "text", text_content: "Test" },
      characters: [],
      narrative_events: [{
        id: "test-1",
        event_type: "OTHER",
        description: "Test",
        agents: null,
        targets: null,
        target_type: "character",
        time_order: 1,
        relationships: [],
        action_layer: { category: "", type: "", context: "", status: "", function: "" }
      }]
    }
  },
  {
    name: "undefined agents/targets",
    json: {
      version: "3.0",
      metadata: { id: "test", title: "Test", culture: "Test" },
      source_info: { language: "en", type: "text", text_content: "Test" },
      characters: [],
      narrative_events: [{
        id: "test-2",
        event_type: "OTHER",
        description: "Test",
        agents: undefined,
        targets: undefined,
        target_type: "character",
        time_order: 1,
        relationships: [],
        action_layer: { category: "", type: "", context: "", status: "", function: "" }
      }]
    }
  },
  {
    name: "missing agents/targets",
    json: {
      version: "3.0",
      metadata: { id: "test", title: "Test", culture: "Test" },
      source_info: { language: "en", type: "text", text_content: "Test" },
      characters: [],
      narrative_events: [{
        id: "test-3",
        event_type: "OTHER",
        description: "Test",
        target_type: "character",
        time_order: 1,
        relationships: [],
        action_layer: { category: "", type: "", context: "", status: "", function: "" }
      }]
    }
  },
  {
    name: "wrong type agents/targets",
    json: {
      version: "3.0",
      metadata: { id: "test", title: "Test", culture: "Test" },
      source_info: { language: "en", type: "text", text_content: "Test" },
      characters: [],
      narrative_events: [{
        id: "test-4",
        event_type: "OTHER",
        description: "Test",
        agents: "string",
        targets: 123,
        target_type: "character",
        time_order: 1,
        relationships: [],
        action_layer: { category: "", type: "", context: "", status: "", function: "" }
      }]
    }
  },
  {
    name: "null relationships",
    json: {
      version: "3.0",
      metadata: { id: "test", title: "Test", culture: "Test" },
      source_info: { language: "en", type: "text", text_content: "Test" },
      characters: [],
      narrative_events: [{
        id: "test-5",
        event_type: "OTHER",
        description: "Test",
        agents: [],
        targets: [],
        target_type: "character",
        time_order: 1,
        relationships: null,
        action_layer: { category: "", type: "", context: "", status: "", function: "" }
      }]
    }
  },
  {
    name: "missing relationships",
    json: {
      version: "3.0",
      metadata: { id: "test", title: "Test", culture: "Test" },
      source_info: { language: "en", type: "text", text_content: "Test" },
      characters: [],
      narrative_events: [{
        id: "test-6",
        event_type: "OTHER",
        description: "Test",
        agents: [],
        targets: [],
        target_type: "character",
        time_order: 1,
        action_layer: { category: "", type: "", context: "", status: "", function: "" }
      }]
    }
  },
  {
    name: "null action_layer",
    json: {
      version: "3.0",
      metadata: { id: "test", title: "Test", culture: "Test" },
      source_info: { language: "en", type: "text", text_content: "Test" },
      characters: [],
      narrative_events: [{
        id: "test-7",
        event_type: "OTHER",
        description: "Test",
        agents: [],
        targets: [],
        target_type: "character",
        time_order: 1,
        relationships: [],
        action_layer: null
      }]
    }
  },
  {
    name: "missing action_layer",
    json: {
      version: "3.0",
      metadata: { id: "test", title: "Test", culture: "Test" },
      source_info: { language: "en", type: "text", text_content: "Test" },
      characters: [],
      narrative_events: [{
        id: "test-8",
        event_type: "OTHER",
        description: "Test",
        agents: [],
        targets: [],
        target_type: "character",
        time_order: 1,
        relationships: []
      }]
    }
  },
  {
    name: "missing id",
    json: {
      version: "3.0",
      metadata: { id: "test", title: "Test", culture: "Test" },
      source_info: { language: "en", type: "text", text_content: "Test" },
      characters: [],
      narrative_events: [{
        event_type: "OTHER",
        description: "Test",
        agents: [],
        targets: [],
        target_type: "character",
        time_order: 1,
        relationships: [],
        action_layer: { category: "", type: "", context: "", status: "", function: "" }
      }]
    }
  },
  {
    name: "missing time_order",
    json: {
      version: "3.0",
      metadata: { id: "test", title: "Test", culture: "Test" },
      source_info: { language: "en", type: "text", text_content: "Test" },
      characters: [],
      narrative_events: [{
        id: "test-10",
        event_type: "OTHER",
        description: "Test",
        agents: [],
        targets: [],
        target_type: "character",
        relationships: [],
        action_layer: { category: "", type: "", context: "", status: "", function: "" }
      }]
    }
  }
];

let passed = 0;
let failed = 0;

testCases.forEach((testCase, index) => {
  console.log(`Test ${index + 1}: ${testCase.name}`);
  
  try {
    const loadedState = mapV3ToState(testCase.json);
    const events = loadedState.narrativeStructure || [];
    
    if (events.length === 0) {
      console.log(`  ✗ No events loaded\n`);
      failed++;
      return;
    }
    
    const event = events[0];
    if (typeof event === 'string') {
      console.log(`  ⚠ Event is string type (unexpected)\n`);
      failed++;
      return;
    }
    
    // Validate the event has all required fields
    const issues = [];
    if (!event.id) issues.push('missing id');
    if (!Array.isArray(event.agents)) issues.push('agents not array');
    if (!Array.isArray(event.targets)) issues.push('targets not array');
    if (!Array.isArray(event.relationship_multi)) issues.push('relationship_multi not array');
    if (event.time_order === undefined) issues.push('missing time_order');
    
    if (issues.length > 0) {
      console.log(`  ✗ Issues: ${issues.join(', ')}\n`);
      failed++;
    } else {
      console.log(`  ✓ Loaded successfully (id: ${event.id}, agents: ${event.agents.length}, targets: ${event.targets.length}, relationships: ${event.relationship_multi.length})\n`);
      passed++;
    }
  } catch (error) {
    console.log(`  ✗ Error: ${error.message}\n`);
    failed++;
  }
});

console.log('=== Summary ===');
console.log(`Passed: ${passed}/${testCases.length}`);
console.log(`Failed: ${failed}/${testCases.length}`);

if (failed === 0) {
  console.log('\n✓ Loading logic handles all defective cases correctly');
} else {
  console.log('\n✗ Some defective cases cause issues');
}

process.exit(failed > 0 ? 1 : 0);
