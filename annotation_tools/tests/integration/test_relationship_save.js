// Test relationship saving in v3
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PROJECT_ROOT = path.resolve(__dirname, '..', '..');

console.log('=== Testing Relationship Save in V3 ===\n');

// Load a v3 JSON file
const testFile = path.join(PROJECT_ROOT, '..', 'datasets/Japanese_test/json_v3/jp_003_v3.json');
const data = JSON.parse(fs.readFileSync(testFile, 'utf8'));

console.log('Checking narrative_events relationships...\n');

let totalEvents = 0;
let eventsWithRelationships = 0;
let eventsWithEmptyRelationships = 0;
let issues = [];

data.narrative_events?.forEach((event, index) => {
  totalEvents++;
  
  // Check if relationships field exists
  if (!('relationships' in event)) {
    issues.push(`Event ${index} (${event.id}): Missing 'relationships' field`);
    return;
  }
  
  // Check if relationships is an array
  if (!Array.isArray(event.relationships)) {
    issues.push(`Event ${index} (${event.id}): 'relationships' is not an array (type: ${typeof event.relationships})`);
    return;
  }
  
  if (event.relationships.length > 0) {
    eventsWithRelationships++;
    
    // Validate each relationship
    event.relationships.forEach((rel, relIndex) => {
      const relIssues = [];
      
      if (!rel || typeof rel !== 'object') {
        relIssues.push(`Relationship ${relIndex} is not an object`);
      } else {
        if (rel.agent === undefined) relIssues.push(`Missing 'agent'`);
        if (rel.target === undefined) relIssues.push(`Missing 'target'`);
        if (rel.relationship_level1 === undefined) relIssues.push(`Missing 'relationship_level1'`);
        if (rel.relationship_level2 === undefined) relIssues.push(`Missing 'relationship_level2'`);
        if (rel.sentiment === undefined) relIssues.push(`Missing 'sentiment'`);
      }
      
      if (relIssues.length > 0) {
        issues.push(`Event ${index} (${event.id}), Relationship ${relIndex}: ${relIssues.join(', ')}`);
      }
    });
    
    // Show sample
    if (index < 2) {
      console.log(`Event ${index} (${event.id}):`);
      console.log(`  Relationships: ${event.relationships.length}`);
      event.relationships.forEach((rel, relIdx) => {
        console.log(`    [${relIdx}] agent: "${rel.agent}", target: "${rel.target}", level1: "${rel.relationship_level1}", level2: "${rel.relationship_level2}", sentiment: "${rel.sentiment}"`);
      });
      console.log();
    }
  } else {
    eventsWithEmptyRelationships++;
  }
});

console.log('=== Summary ===');
console.log(`Total events: ${totalEvents}`);
console.log(`Events with relationships: ${eventsWithRelationships}`);
console.log(`Events with empty relationships: ${eventsWithEmptyRelationships}`);
console.log(`Issues found: ${issues.length}\n`);

if (issues.length > 0) {
  console.log('=== Issues ===');
  issues.forEach(issue => console.log(`  ✗ ${issue}`));
} else {
  console.log('✓ All relationships are correctly formatted');
}

// Check for unwanted flat fields
console.log('\n=== Checking for Unwanted Flat Fields ===');
let flatFieldIssues = [];
data.narrative_events?.forEach((event, index) => {
  if (event.relationship_level1 !== undefined) {
    flatFieldIssues.push(`Event ${index} (${event.id}): Has relationship_level1 at event level`);
  }
  if (event.relationship_level2 !== undefined) {
    flatFieldIssues.push(`Event ${index} (${event.id}): Has relationship_level2 at event level`);
  }
  if (event.sentiment !== undefined) {
    flatFieldIssues.push(`Event ${index} (${event.id}): Has sentiment at event level`);
  }
});

if (flatFieldIssues.length > 0) {
  console.log(`✗ Found ${flatFieldIssues.length} events with unwanted flat fields:`);
  flatFieldIssues.forEach(issue => console.log(`  - ${issue}`));
} else {
  console.log('✓ No unwanted flat fields found');
}

process.exit(issues.length > 0 || flatFieldIssues.length > 0 ? 1 : 0);
