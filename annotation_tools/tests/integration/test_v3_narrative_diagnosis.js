// Diagnostic test for v3 narrative_events save issues
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { mapV3ToState } from '../../src/utils/fileHandler.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PROJECT_ROOT = path.resolve(__dirname, '..', '..');

console.log('=== V3 Narrative Events Save Diagnosis ===\n');

// Load test file
const testFile = path.join(PROJECT_ROOT, '..', 'datasets/Japanese_test/json_v3/jp_003_v3.json');
const data = JSON.parse(fs.readFileSync(testFile, 'utf8'));

// Map to state
const state = mapV3ToState(data);

console.log('=== State Analysis ===');
console.log(`Total narrative events in state: ${state.narrativeStructure.length}\n`);

// Analyze each event in state
state.narrativeStructure.forEach((event, index) => {
  if (typeof event === 'string') {
    console.log(`Event ${index}: String type - "${event.substring(0, 50)}..."`);
    return;
  }

  console.log(`\nEvent ${index} (${event.id || 'NO ID'}):`);
  console.log(`  event_type: ${event.event_type || 'MISSING'}`);
  console.log(`  description: ${event.description ? event.description.substring(0, 50) + '...' : 'EMPTY'}`);
  console.log(`  agents: [${(event.agents || []).join(', ')}]`);
  console.log(`  targets: [${(event.targets || []).join(', ')}]`);
  console.log(`  time_order: ${event.time_order ?? 'MISSING'}`);
  
  // Check relationship data
  const hasRelationshipMulti = Array.isArray(event.relationship_multi) && event.relationship_multi.length > 0;
  const hasLegacyFields = !!(event.relationship_level1 || event.relationship_level2 || event.sentiment);
  
  console.log(`  relationship_multi: ${hasRelationshipMulti ? `${event.relationship_multi.length} entries` : 'empty'}`);
  if (hasRelationshipMulti) {
    event.relationship_multi.forEach((rel, relIdx) => {
      console.log(`    [${relIdx}] agent: "${rel.agent}", target: "${rel.target}", level1: "${rel.relationship_level1}", level2: "${rel.relationship_level2}", sentiment: "${rel.sentiment}"`);
    });
  }
  console.log(`  legacy fields: ${hasLegacyFields ? `level1="${event.relationship_level1}", level2="${event.relationship_level2}", sentiment="${event.sentiment}"` : 'none'}`);
  
  // Check action data
  const hasActionLayer = !!(event.action_category || event.action_type || event.action_context || event.action_status || event.narrative_function);
  console.log(`  action fields: ${hasActionLayer ? `category="${event.action_category}", type="${event.action_type}", function="${event.narrative_function}"` : 'none'}`);
  
  // Predict what would be saved
  const agents = Array.isArray(event.agents) ? event.agents.filter(Boolean) : [];
  const targets = Array.isArray(event.targets) ? event.targets.filter(Boolean) : [];
  
  const existingMultiList = Array.isArray(event.relationship_multi)
    ? event.relationship_multi
    : ((event.relationship_multi && typeof event.relationship_multi === "object") ? [event.relationship_multi] : []);

  let relList = [];
  if (existingMultiList.length > 0) {
    relList = existingMultiList.map(r => ({
      agent: r.agent || "",
      target: r.target || "",
      relationship_level1: r.relationship_level1 || "",
      relationship_level2: r.relationship_level2 || "",
      sentiment: r.sentiment || ""
    }));
  } else if (event.relationship_level1 || event.relationship_level2 || event.sentiment) {
    relList = [{
      agent: agents[0] || "",
      target: targets[0] || "",
      relationship_level1: event.relationship_level1 || "",
      relationship_level2: event.relationship_level2 || "",
      sentiment: event.sentiment || ""
    }];
  }
  
  console.log(`  → Would save ${relList.length} relationships`);
  if (relList.length > 0) {
    relList.forEach((rel, relIdx) => {
      console.log(`    [${relIdx}] agent: "${rel.agent}", target: "${rel.target}", level1: "${rel.relationship_level1}"`);
    });
  }
  
  // Check for potential issues
  const issues = [];
  if (!event.id) issues.push('Missing id');
  if (event.time_order === undefined) issues.push('Missing time_order');
  if (hasRelationshipMulti && hasLegacyFields) {
    issues.push('Has both relationship_multi and legacy fields (may cause confusion)');
  }
  if (hasRelationshipMulti && relList.length === 0) {
    issues.push('Has relationship_multi but would save empty relationships array');
  }
  if (!hasRelationshipMulti && !hasLegacyFields && relList.length > 0) {
    issues.push('Would create relationship from empty data');
  }
  
  if (issues.length > 0) {
    console.log(`  ⚠ Issues: ${issues.join(', ')}`);
  } else {
    console.log(`  ✓ No issues detected`);
  }
});

// Compare with original
console.log('\n\n=== Original JSON Comparison ===');
const originalEvents = data.narrative_events || [];
console.log(`Original events: ${originalEvents.length}`);

originalEvents.forEach((event, index) => {
  const stateEvent = state.narrativeStructure[index];
  if (!stateEvent || typeof stateEvent === 'string') {
    console.log(`\nEvent ${index} (${event.id}):`);
    console.log(`  ⚠ State event is string or missing`);
    return;
  }
  
  const originalRelCount = event.relationships?.length || 0;
  const stateRelCount = (Array.isArray(stateEvent.relationship_multi) ? stateEvent.relationship_multi.length : 0) ||
                        (stateEvent.relationship_level1 ? 1 : 0);
  
  if (originalRelCount !== stateRelCount) {
    console.log(`\nEvent ${index} (${event.id}):`);
    console.log(`  ⚠ Relationship count mismatch: original=${originalRelCount}, state=${stateRelCount}`);
  }
});

console.log('\n=== Diagnosis Complete ===');
