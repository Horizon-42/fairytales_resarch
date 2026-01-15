// Test v3 save/load roundtrip for narrative_events
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { mapV3ToState } from '../../src/utils/fileHandler.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PROJECT_ROOT = path.resolve(__dirname, '..', '..');

console.log('=== Testing v3 Save/Load Roundtrip for Narrative Events ===\n');

// Load a v3 JSON file
const testFile = path.join(PROJECT_ROOT, '..', 'datasets/Japanese_test/json_v3/jp_003_v3.json');

if (!fs.existsSync(testFile)) {
  console.error(`Test file not found: ${testFile}`);
  process.exit(1);
}

const originalData = JSON.parse(fs.readFileSync(testFile, 'utf8'));
console.log('✓ Loaded original v3 JSON file\n');

// Simulate loading: map JSON to state
const loadedState = mapV3ToState(originalData);
console.log('✓ Mapped JSON to state\n');

// Check narrative structure
console.log('=== Loaded State Check ===');
console.log(`Narrative events in state: ${loadedState.narrativeStructure?.length || 0}`);

// Simulate what would be saved (simplified version of jsonV3 logic)
const simulateSave = (state) => {
  return state.narrativeStructure.map((n, index) => {
    if (typeof n === "string") {
      return {
        id: `generated-${index}`,
        text_span: null,
        event_type: "OTHER",
        description: n,
        agents: [],
        targets: [],
        target_type: "character",
        object_type: "",
        instrument: "",
        time_order: index + 1,
        relationships: [],
        action_layer: {
          category: "",
          type: "",
          context: "",
          status: "",
          function: ""
        }
      };
    }

    const agents = Array.isArray(n.agents) ? n.agents.filter(Boolean) : [];
    const targets = Array.isArray(n.targets) ? n.targets.filter(Boolean) : [];
    
    const existingMultiList = Array.isArray(n.relationship_multi)
      ? n.relationship_multi
      : ((n.relationship_multi && typeof n.relationship_multi === "object") ? [n.relationship_multi] : []);

    let relList = [];
    if (existingMultiList.length > 0) {
      relList = existingMultiList.map(r => ({
        agent: r.agent || "",
        target: r.target || "",
        relationship_level1: r.relationship_level1 || "",
        relationship_level2: r.relationship_level2 || "",
        sentiment: r.sentiment || ""
      }));
    } else if (n.relationship_level1 || n.relationship_level2 || n.sentiment) {
      relList = [{
        agent: agents[0] || "",
        target: targets[0] || "",
        relationship_level1: n.relationship_level1 || "",
        relationship_level2: n.relationship_level2 || "",
        sentiment: n.sentiment || ""
      }];
    }

    const actionLayer = {
      category: n.action_category || "",
      type: n.action_type || "",
      context: n.action_context || "",
      status: n.action_status || "",
      function: n.narrative_function || ""
    };

    return {
      id: n.id || `generated-${index}`,
      text_span: n.text_span || null,
      event_type: n.event_type || "",
      description: n.description || "",
      agents: agents,
      targets: targets,
      target_type: n.target_type || "character",
      object_type: n.object_type || "",
      instrument: n.instrument || "",
      time_order: n.time_order ?? (index + 1),
      relationships: relList,
      action_layer: actionLayer
    };
  });
};

const savedEvents = simulateSave(loadedState);
const originalEvents = originalData.narrative_events || [];

console.log('=== Roundtrip Comparison ===');
console.log(`Original events: ${originalEvents.length}`);
console.log(`Saved events: ${savedEvents.length}\n`);

// Compare events
let differences = [];
let matches = 0;

for (let i = 0; i < Math.max(originalEvents.length, savedEvents.length); i++) {
  const original = originalEvents[i];
  const saved = savedEvents[i];
  
  if (!original && saved) {
    differences.push(`Event ${i}: Original missing, but would be saved`);
    continue;
  }
  if (original && !saved) {
    differences.push(`Event ${i}: Original exists, but would not be saved`);
    continue;
  }
  if (!original && !saved) continue;

  const eventDiff = [];
  
  // Compare key fields
  if (original.id !== saved.id) eventDiff.push(`id: ${original.id} vs ${saved.id}`);
  if (JSON.stringify(original.text_span) !== JSON.stringify(saved.text_span)) {
    eventDiff.push(`text_span differs`);
  }
  if (original.event_type !== saved.event_type) {
    eventDiff.push(`event_type: ${original.event_type} vs ${saved.event_type}`);
  }
  if (original.description !== saved.description) {
    eventDiff.push(`description differs`);
  }
  if (JSON.stringify(original.agents) !== JSON.stringify(saved.agents)) {
    eventDiff.push(`agents differ`);
  }
  if (JSON.stringify(original.targets) !== JSON.stringify(saved.targets)) {
    eventDiff.push(`targets differ`);
  }
  if (original.time_order !== saved.time_order) {
    eventDiff.push(`time_order: ${original.time_order} vs ${saved.time_order}`);
  }
  
  // Compare relationships
  if (JSON.stringify(original.relationships) !== JSON.stringify(saved.relationships)) {
    eventDiff.push(`relationships differ`);
    console.log(`  Original relationships: ${JSON.stringify(original.relationships)}`);
    console.log(`  Saved relationships: ${JSON.stringify(saved.relationships)}`);
  }
  
  // Compare action_layer
  if (JSON.stringify(original.action_layer) !== JSON.stringify(saved.action_layer)) {
    eventDiff.push(`action_layer differs`);
  }

  if (eventDiff.length > 0) {
    differences.push(`Event ${i} (${original.id}): ${eventDiff.join(', ')}`);
  } else {
    matches++;
  }
}

console.log(`Matching events: ${matches}/${originalEvents.length}`);
if (differences.length > 0) {
  console.log(`\n=== Differences Found ===`);
  differences.forEach(diff => console.log(`  ✗ ${diff}`));
} else {
  console.log(`\n✓ All events match perfectly!`);
}

// Check for data loss
console.log('\n=== Data Loss Check ===');
const originalRelCount = originalEvents.reduce((sum, e) => sum + (e.relationships?.length || 0), 0);
const savedRelCount = savedEvents.reduce((sum, e) => sum + (e.relationships?.length || 0), 0);
console.log(`Original relationships: ${originalRelCount}`);
console.log(`Saved relationships: ${savedRelCount}`);

if (originalRelCount !== savedRelCount) {
  console.log(`  ✗ Relationship count mismatch!`);
} else {
  console.log(`  ✓ Relationship count matches`);
}

// Summary
console.log('\n=== Summary ===');
if (differences.length === 0 && originalRelCount === savedRelCount) {
  console.log('✓ Save/load roundtrip is perfect - no data loss');
} else {
  console.log(`✗ Found ${differences.length} differences`);
  console.log('Please review the differences above');
}

process.exit(differences.length > 0 || originalRelCount !== savedRelCount ? 1 : 0);
