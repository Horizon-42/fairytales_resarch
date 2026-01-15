// Test loading defective v3 JSON files (with null agents/targets)
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { mapV3ToState } from '../../src/utils/fileHandler.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PROJECT_ROOT = path.resolve(__dirname, '..', '..');

console.log('=== Testing Loading Defective V3 JSON ===\n');

// Create a test defective JSON
const defectiveJSON = {
  version: "3.0",
  metadata: {
    id: "test",
    title: "Test",
    culture: "Test"
  },
  source_info: {
    language: "en",
    type: "text",
    text_content: "Test content"
  },
  characters: [],
  narrative_events: [
    {
      id: "test-1",
      event_type: "OTHER",
      description: "Test event",
      agents: null,  // Defective: null instead of array
      targets: null,  // Defective: null instead of array
      target_type: "character",
      object_type: "",
      instrument: "",
      time_order: 1,
      relationships: [],
      action_layer: {
        category: "",
        type: "",
        context: "",
        status: "",
        function: ""
      }
    },
    {
      id: "test-2",
      event_type: "DEPARTURE",
      description: "Another test",
      agents: undefined,  // Defective: undefined
      targets: undefined,  // Defective: undefined
      target_type: "character",
      object_type: "",
      instrument: "",
      time_order: 2,
      relationships: [],
      action_layer: {
        category: "",
        type: "",
        context: "",
        status: "",
        function: ""
      }
    },
    {
      id: "test-3",
      event_type: "VILLAINY",
      description: "Third test",
      // Missing agents and targets entirely
      target_type: "character",
      object_type: "",
      instrument: "",
      time_order: 3,
      relationships: [],
      action_layer: {
        category: "",
        type: "",
        context: "",
        status: "",
        function: ""
      }
    },
    {
      id: "test-4",
      event_type: "HERO_REACTION",
      description: "Fourth test",
      agents: "not-an-array",  // Defective: string instead of array
      targets: 123,  // Defective: number instead of array
      target_type: "character",
      object_type: "",
      instrument: "",
      time_order: 4,
      relationships: [],
      action_layer: {
        category: "",
        type: "",
        context: "",
        status: "",
        function: ""
      }
    }
  ]
};

console.log('Testing with defective JSON (null, undefined, missing, wrong type)...\n');

try {
  const loadedState = mapV3ToState(defectiveJSON);
  console.log('✓ Successfully loaded defective JSON\n');
  
  console.log('=== Checking Loaded State ===');
  const events = loadedState.narrativeStructure || [];
  console.log(`Loaded ${events.length} events\n`);
  
  let allValid = true;
  events.forEach((event, index) => {
    if (typeof event === 'string') {
      console.log(`Event ${index}: String type (skipping validation)`);
      return;
    }
    
    const issues = [];
    
    // Check agents
    if (!Array.isArray(event.agents)) {
      issues.push(`agents is not an array (type: ${typeof event.agents}, value: ${JSON.stringify(event.agents)})`);
      allValid = false;
    }
    
    // Check targets
    if (!Array.isArray(event.targets)) {
      issues.push(`targets is not an array (type: ${typeof event.targets}, value: ${JSON.stringify(event.targets)})`);
      allValid = false;
    }
    
    if (issues.length > 0) {
      console.log(`✗ Event ${index} (${event.id}):`);
      issues.forEach(issue => console.log(`  - ${issue}`));
    } else {
      console.log(`✓ Event ${index} (${event.id}): agents=[${event.agents.join(', ')}], targets=[${event.targets.join(', ')}]`);
    }
  });
  
  console.log('\n=== Summary ===');
  if (allValid) {
    console.log('✓ All events have valid agents and targets arrays');
    console.log('✓ Loading logic correctly handles defective JSON');
  } else {
    console.log('✗ Some events have invalid agents/targets');
    console.log('✗ Loading logic needs improvement');
  }
  
  process.exit(allValid ? 0 : 1);
  
} catch (error) {
  console.error('✗ Error loading defective JSON:');
  console.error(error);
  console.error('\n✗ Loading logic cannot handle defective JSON');
  process.exit(1);
}
