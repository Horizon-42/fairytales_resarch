// Simulate relationship save process to debug
import { fileURLToPath } from 'url';
import path from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

console.log('=== Simulating Relationship Save Process ===\n');

// Simulate UI state (what narrativeStructure looks like in state)
const simulateUIState = [
  {
    id: "test-1",
    event_type: "DEPARTURE",
    description: "Test event",
    agents: ["Character A", "Character B"],
    targets: ["Character C"],
    target_type: "character",
    time_order: 1,
    // Case 1: Has relationship_multi (correct)
    relationship_multi: [
      {
        agent: "Character A",
        target: "Character C",
        relationship_level1: "Romance",
        relationship_level2: "lover",
        sentiment: "positive"
      }
    ],
    relationship_level1: "",  // Empty because multi-relationship
    relationship_level2: "",
    sentiment: ""
  },
  {
    id: "test-2",
    event_type: "VILLAINY",
    description: "Another event",
    agents: ["Character D"],
    targets: ["Character E"],
    target_type: "character",
    time_order: 2,
    // Case 2: No relationship_multi, but has legacy fields (should work)
    relationship_multi: [],
    relationship_level1: "Family & Kinship",
    relationship_level2: "parent_child",
    sentiment: "neutral"
  },
  {
    id: "test-3",
    event_type: "HERO_REACTION",
    description: "Third event",
    agents: ["Character F"],
    targets: ["Character G"],
    target_type: "character",
    time_order: 3,
    // Case 3: Empty relationship_multi and no legacy fields
    relationship_multi: [],
    relationship_level1: "",
    relationship_level2: "",
    sentiment: ""
  },
  {
    id: "test-4",
    event_type: "WEDDING",
    description: "Fourth event",
    agents: ["Character H", "Character I"],
    targets: ["Character J"],
    target_type: "character",
    time_order: 4,
    // Case 4: Multiple relationships in relationship_multi
    relationship_multi: [
      {
        agent: "Character H",
        target: "Character J",
        relationship_level1: "Romance",
        relationship_level2: "spouse",
        sentiment: "positive"
      },
      {
        agent: "Character I",
        target: "Character J",
        relationship_level1: "Family & Kinship",
        relationship_level2: "sibling",
        sentiment: "neutral"
      }
    ],
    relationship_level1: "",
    relationship_level2: "",
    sentiment: ""
  }
];

// Simulate the save logic (from App.jsx jsonV3)
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

const simulateSave = (narrativeStructure) => {
  return narrativeStructure.map((n, index) => {
    if (typeof n === "string") {
      return {
        id: `generated-${index}`,
        event_type: "OTHER",
        description: n,
        agents: [],
        targets: [],
        relationships: [],
        action_layer: { category: "", type: "", context: "", status: "", function: "" }
      };
    }

    const agents = Array.isArray(n.agents) ? n.agents.filter(Boolean) : [];
    const targets = Array.isArray(n.targets) ? n.targets.filter(Boolean) : [];

    // v3: extract relationships from relationship_multi (UI state) or flat fields
    const existingMultiList = Array.isArray(n.relationship_multi)
      ? n.relationship_multi
      : ((n.relationship_multi && typeof n.relationship_multi === "object") ? [n.relationship_multi] : []);

    console.log(`\nEvent ${index} (${n.id}):`);
    console.log(`  relationship_multi: ${JSON.stringify(existingMultiList)}`);
    console.log(`  legacy fields: level1="${n.relationship_level1}", level2="${n.relationship_level2}", sentiment="${n.sentiment}"`);

    let relList = [];
    if (existingMultiList.length > 0) {
      relList = existingMultiList.map(normalizeRelEntry);
      console.log(`  → Using relationship_multi: ${relList.length} relationships`);
    } else if (n.relationship_level1 || n.relationship_level2 || n.sentiment) {
      relList = [normalizeRelEntry({
        agent: agents[0] || "",
        target: targets[0] || "",
        relationship_level1: n.relationship_level1 || "",
        relationship_level2: n.relationship_level2 || "",
        sentiment: n.sentiment || ""
      })];
      console.log(`  → Using legacy fields: ${relList.length} relationships`);
    } else {
      console.log(`  → No relationships found`);
    }

    return {
      id: n.id,
      event_type: n.event_type || "",
      description: n.description || "",
      agents: agents,
      targets: targets,
      target_type: n.target_type || "character",
      time_order: n.time_order ?? (index + 1),
      relationships: relList,
      action_layer: { category: "", type: "", context: "", status: "", function: "" }
    };
  });
};

const savedEvents = simulateSave(simulateUIState);

console.log('\n=== Saved Results ===');
savedEvents.forEach((event, index) => {
  console.log(`\nEvent ${index} (${event.id}):`);
  console.log(`  Relationships: ${event.relationships.length}`);
  event.relationships.forEach((rel, relIdx) => {
    console.log(`    [${relIdx}] agent: "${rel.agent}", target: "${rel.target}", level1: "${rel.relationship_level1}", level2: "${rel.relationship_level2}", sentiment: "${rel.sentiment}"`);
  });
});

console.log('\n=== Summary ===');
const totalRelationships = savedEvents.reduce((sum, e) => sum + e.relationships.length, 0);
console.log(`Total relationships saved: ${totalRelationships}`);
console.log(`Expected: 4 (1 + 1 + 0 + 2)`);

if (totalRelationships === 4) {
  console.log('✓ Save logic works correctly');
} else {
  console.log(`✗ Save logic issue: expected 4, got ${totalRelationships}`);
}
