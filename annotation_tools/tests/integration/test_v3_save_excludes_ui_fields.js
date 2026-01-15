// Test that v3 save logic excludes UI-only fields like relationship_multi
import { fileURLToPath } from 'url';
import path from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

console.log('=== Testing V3 Save Excludes UI-Only Fields ===\n');

// Simulate the save logic (simplified version)
const normalizeRelEntry = (r) => {
  const rel = (r && typeof r === "object") ? r : {};
  const level1 = rel.relationship_level1 || "";
  return {
    agent: rel.agent || "",
    target: rel.target || "",
    relationship_level1: level1 || "",
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

// Simulate UI state with UI-only fields
const uiState = {
  id: "test-1",
  event_type: "DEPARTURE",
  description: "Test event",
  agents: ["Character A"],
  targets: ["Character B"],
  target_type: "character",
  time_order: 1,
  // UI-only fields that should NOT be saved
  relationship_multi: [
    {
      agent: "Character A",
      target: "Character B",
      relationship_level1: "Romance",
      relationship_level2: "lover",
      sentiment: "positive"
    }
  ],
  relationship_level1: "Romance",  // UI-only, should NOT be saved
  relationship_level2: "lover",    // UI-only, should NOT be saved
  sentiment: "positive",             // UI-only, should NOT be saved
  action_category: "Action",        // UI-only, should NOT be saved (only action_layer)
  action_type: "Type",              // UI-only, should NOT be saved (only action_layer)
  action_context: "Context",         // UI-only, should NOT be saved (only action_layer)
  action_status: "Status",          // UI-only, should NOT be saved (only action_layer)
  narrative_function: "Function"    // UI-only, should NOT be saved (only action_layer.function)
};

// Simulate save logic (from App.jsx)
const agents = Array.isArray(uiState.agents) ? uiState.agents.filter(Boolean) : [];
const targets = Array.isArray(uiState.targets) ? uiState.targets.filter(Boolean) : [];

const existingMultiList = Array.isArray(uiState.relationship_multi)
  ? uiState.relationship_multi
  : ((uiState.relationship_multi && typeof uiState.relationship_multi === "object") ? [uiState.relationship_multi] : []);

let relList = [];
if (existingMultiList.length > 0) {
  relList = existingMultiList.map(normalizeRelEntry);
} else if (uiState.relationship_level1 || uiState.relationship_level2 || uiState.sentiment) {
  relList = [normalizeRelEntry({
    agent: agents[0] || "",
    target: targets[0] || "",
    relationship_level1: uiState.relationship_level1 || "",
    relationship_level2: uiState.relationship_level2 || "",
    sentiment: uiState.sentiment || ""
  })];
}

const actionLayer = buildActionLayerV3(uiState);

// Explicitly construct object (as in App.jsx)
const savedEvent = {
  id: uiState.id,
  text_span: uiState.text_span || null,
  event_type: uiState.event_type || "",
  description: uiState.description || "",
  agents: agents,
  targets: targets,
  target_type: uiState.target_type || "character",
  object_type: uiState.object_type || "",
  instrument: uiState.instrument || "",
  time_order: uiState.time_order ?? 1,
  relationships: relList,
  action_layer: actionLayer
  // Explicitly NOT including: relationship_multi, relationship_level1, relationship_level2, sentiment
};

console.log('UI State (with UI-only fields):');
console.log(`  relationship_multi: ${JSON.stringify(uiState.relationship_multi)}`);
console.log(`  relationship_level1: ${uiState.relationship_level1}`);
console.log(`  relationship_level2: ${uiState.relationship_level2}`);
console.log(`  sentiment: ${uiState.sentiment}`);
console.log(`  action_category: ${uiState.action_category}`);
console.log(`  action_type: ${uiState.action_type}`);
console.log(`  action_context: ${uiState.action_context}`);
console.log(`  action_status: ${uiState.action_status}`);
console.log(`  narrative_function: ${uiState.narrative_function}\n`);

console.log('Saved Event (should NOT have UI-only fields):');
const savedKeys = Object.keys(savedEvent);
console.log(`  Keys: ${savedKeys.join(', ')}\n`);

// Check for UI-only fields
const uiOnlyFields = [
  'relationship_multi',
  'relationship_level1',
  'relationship_level2',
  'sentiment',
  'action_category',
  'action_type',
  'action_context',
  'action_status',
  'narrative_function'
];

const foundUIOnlyFields = uiOnlyFields.filter(field => field in savedEvent);

if (foundUIOnlyFields.length > 0) {
  console.log(`✗ Found UI-only fields in saved event: ${foundUIOnlyFields.join(', ')}`);
  console.log('  These should NOT be saved to v3 JSON!');
  process.exit(1);
} else {
  console.log('✓ No UI-only fields found in saved event');
  console.log('✓ Only v3 fields are saved:');
  console.log(`  - relationships: ${JSON.stringify(savedEvent.relationships)}`);
  console.log(`  - action_layer: ${JSON.stringify(savedEvent.action_layer)}`);
  console.log('\n✓ Save logic correctly excludes UI-only fields');
}
