// Test v3 narrative_events save functionality
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PROJECT_ROOT = path.resolve(__dirname, '..', '..');

console.log('=== Testing v3 Narrative Events Save ===\n');
console.log(`Project root: ${PROJECT_ROOT}`);

// Load a v3 JSON file
const testFile = path.join(PROJECT_ROOT, '..', 'datasets/Japanese_test/json_v3/jp_003_v3.json');
console.log(`Test file: ${testFile}`);

if (!fs.existsSync(testFile)) {
  console.error(`Test file not found: ${testFile}`);
  process.exit(1);
}

const data = JSON.parse(fs.readFileSync(testFile, 'utf8'));

console.log('✓ Loaded v3 JSON file\n');

// Check structure
console.log('=== Structure Check ===');
console.log(`Version: ${data.version}`);
console.log(`Narrative events count: ${data.narrative_events?.length || 0}\n`);

// Validate each narrative event
let issues = [];
let validCount = 0;

data.narrative_events?.forEach((event, index) => {
  const eventId = event.id || `event_${index}`;
  const issuesForEvent = [];

  // Required fields
  if (!event.id) issuesForEvent.push('Missing id');
  if (event.event_type === undefined) issuesForEvent.push('Missing event_type');
  if (event.description === undefined) issuesForEvent.push('Missing description');
  if (!Array.isArray(event.agents)) issuesForEvent.push('agents is not an array');
  if (!Array.isArray(event.targets)) issuesForEvent.push('targets is not an array');
  if (event.time_order === undefined) issuesForEvent.push('Missing time_order');

  // v3 specific: should have relationships array (not flat fields)
  if (!Array.isArray(event.relationships)) {
    issuesForEvent.push('relationships is not an array');
  }

  // v3 specific: should have action_layer object (not flat fields)
  if (!event.action_layer || typeof event.action_layer !== 'object') {
    issuesForEvent.push('action_layer is missing or not an object');
  }

  // v3 should NOT have flat relationship fields
  if (event.relationship_level1 !== undefined) {
    issuesForEvent.push('Should not have relationship_level1 (v3 uses relationships array)');
  }
  if (event.relationship_level2 !== undefined) {
    issuesForEvent.push('Should not have relationship_level2 (v3 uses relationships array)');
  }
  if (event.sentiment !== undefined) {
    issuesForEvent.push('Should not have sentiment (v3 uses relationships array)');
  }

  // v3 should NOT have flat action fields
  if (event.action_category !== undefined) {
    issuesForEvent.push('Should not have action_category (v3 uses action_layer)');
  }
  if (event.action_type !== undefined) {
    issuesForEvent.push('Should not have action_type (v3 uses action_layer)');
  }
  if (event.action_context !== undefined) {
    issuesForEvent.push('Should not have action_context (v3 uses action_layer)');
  }
  if (event.action_status !== undefined) {
    issuesForEvent.push('Should not have action_status (v3 uses action_layer)');
  }
  if (event.narrative_function !== undefined) {
    issuesForEvent.push('Should not have narrative_function (v3 uses action_layer.function)');
  }

  // Validate relationships structure
  if (Array.isArray(event.relationships)) {
    event.relationships.forEach((rel, relIndex) => {
      if (!rel || typeof rel !== 'object') {
        issuesForEvent.push(`Relationship ${relIndex} is not an object`);
      } else {
        if (rel.agent === undefined) issuesForEvent.push(`Relationship ${relIndex} missing agent`);
        if (rel.target === undefined) issuesForEvent.push(`Relationship ${relIndex} missing target`);
        if (rel.relationship_level1 === undefined) issuesForEvent.push(`Relationship ${relIndex} missing relationship_level1`);
        if (rel.relationship_level2 === undefined) issuesForEvent.push(`Relationship ${relIndex} missing relationship_level2`);
        if (rel.sentiment === undefined) issuesForEvent.push(`Relationship ${relIndex} missing sentiment`);
      }
    });
  }

  // Validate action_layer structure
  if (event.action_layer && typeof event.action_layer === 'object') {
    const al = event.action_layer;
    if (al.category === undefined) issuesForEvent.push('action_layer missing category');
    if (al.type === undefined) issuesForEvent.push('action_layer missing type');
    if (al.context === undefined) issuesForEvent.push('action_layer missing context');
    if (al.status === undefined) issuesForEvent.push('action_layer missing status');
    if (al.function === undefined) issuesForEvent.push('action_layer missing function');
  }

  if (issuesForEvent.length > 0) {
    issues.push({ eventId, index, issues: issuesForEvent });
  } else {
    validCount++;
  }
});

// Report results
console.log('=== Validation Results ===');
console.log(`Valid events: ${validCount}/${data.narrative_events?.length || 0}`);
console.log(`Events with issues: ${issues.length}\n`);

if (issues.length > 0) {
  console.log('=== Issues Found ===');
  issues.forEach(({ eventId, index, issues: eventIssues }) => {
    console.log(`\nEvent ${index} (${eventId}):`);
    eventIssues.forEach(issue => console.log(`  ✗ ${issue}`));
  });
} else {
  console.log('✓ All narrative events are valid!\n');
}

// Check for common patterns
console.log('=== Pattern Check ===');
const eventsWithRelationships = data.narrative_events?.filter(e => e.relationships?.length > 0) || [];
const eventsWithEmptyRelationships = data.narrative_events?.filter(e => Array.isArray(e.relationships) && e.relationships.length === 0) || [];
const eventsWithActionLayer = data.narrative_events?.filter(e => e.action_layer && typeof e.action_layer === 'object') || [];

console.log(`Events with relationships: ${eventsWithRelationships.length}`);
console.log(`Events with empty relationships array: ${eventsWithEmptyRelationships.length}`);
console.log(`Events with action_layer: ${eventsWithActionLayer.length}`);

// Check relationship data
if (eventsWithRelationships.length > 0) {
  console.log('\n=== Relationship Data Sample ===');
  const sampleEvent = eventsWithRelationships[0];
  console.log(`Event: ${sampleEvent.id}`);
  console.log(`Relationships: ${JSON.stringify(sampleEvent.relationships, null, 2)}`);
}

// Summary
console.log('\n=== Summary ===');
if (issues.length === 0) {
  console.log('✓ All narrative events are correctly formatted for v3');
  console.log('✓ No flat fields found (relationships and action_layer are nested)');
  console.log('✓ All required fields are present');
} else {
  console.log(`✗ Found ${issues.length} events with issues`);
  console.log('Please review the issues above');
}

process.exit(issues.length > 0 ? 1 : 0);
