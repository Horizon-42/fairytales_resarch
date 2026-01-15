// Validate v3 save output - check for unwanted fields
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PROJECT_ROOT = path.resolve(__dirname, '..', '..');

console.log('=== V3 Save Validation ===\n');

// Check all v3 JSON files in test dataset
const testDir = path.join(PROJECT_ROOT, '..', 'datasets/Japanese_test/json_v3');
const files = fs.readdirSync(testDir).filter(f => f.endsWith('.json'));

console.log(`Found ${files.length} v3 JSON files\n`);

let totalIssues = 0;

files.forEach(file => {
  const filePath = path.join(testDir, file);
  const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
  
  console.log(`\n=== ${file} ===`);
  
  const issues = [];
  const events = data.narrative_events || [];
  
  events.forEach((event, index) => {
    const eventIssues = [];
    
    // Check for unwanted flat relationship fields at event level
    if (event.relationship_level1 !== undefined) {
      eventIssues.push('Has relationship_level1 at event level (should be in relationships array)');
    }
    if (event.relationship_level2 !== undefined) {
      eventIssues.push('Has relationship_level2 at event level (should be in relationships array)');
    }
    if (event.sentiment !== undefined) {
      eventIssues.push('Has sentiment at event level (should be in relationships array)');
    }
    
    // Check for unwanted flat action fields at event level
    if (event.action_category !== undefined) {
      eventIssues.push('Has action_category at event level (should be in action_layer)');
    }
    if (event.action_type !== undefined) {
      eventIssues.push('Has action_type at event level (should be in action_layer)');
    }
    if (event.action_context !== undefined) {
      eventIssues.push('Has action_context at event level (should be in action_layer)');
    }
    if (event.action_status !== undefined) {
      eventIssues.push('Has action_status at event level (should be in action_layer)');
    }
    if (event.narrative_function !== undefined) {
      eventIssues.push('Has narrative_function at event level (should be in action_layer.function)');
    }
    
    // Check required fields
    if (!event.id) eventIssues.push('Missing id');
    if (event.event_type === undefined) eventIssues.push('Missing event_type');
    if (!Array.isArray(event.agents)) eventIssues.push('agents is not an array');
    if (!Array.isArray(event.targets)) eventIssues.push('targets is not an array');
    if (!Array.isArray(event.relationships)) {
      eventIssues.push('relationships is not an array');
    }
    if (!event.action_layer || typeof event.action_layer !== 'object') {
      eventIssues.push('action_layer is missing or not an object');
    }
    
    // Check relationships structure
    if (Array.isArray(event.relationships)) {
      event.relationships.forEach((rel, relIdx) => {
        if (!rel || typeof rel !== 'object') {
          eventIssues.push(`Relationship ${relIdx} is not an object`);
        } else {
          if (rel.agent === undefined) eventIssues.push(`Relationship ${relIdx} missing agent`);
          if (rel.target === undefined) eventIssues.push(`Relationship ${relIdx} missing target`);
          if (rel.relationship_level1 === undefined) {
            eventIssues.push(`Relationship ${relIdx} missing relationship_level1`);
          }
          if (rel.relationship_level2 === undefined) {
            eventIssues.push(`Relationship ${relIdx} missing relationship_level2`);
          }
          if (rel.sentiment === undefined) {
            eventIssues.push(`Relationship ${relIdx} missing sentiment`);
          }
        }
      });
    }
    
    // Check action_layer structure
    if (event.action_layer && typeof event.action_layer === 'object') {
      const al = event.action_layer;
      if (al.category === undefined) eventIssues.push('action_layer missing category');
      if (al.type === undefined) eventIssues.push('action_layer missing type');
      if (al.context === undefined) eventIssues.push('action_layer missing context');
      if (al.status === undefined) eventIssues.push('action_layer missing status');
      if (al.function === undefined) eventIssues.push('action_layer missing function');
    }
    
    if (eventIssues.length > 0) {
      issues.push({ eventIndex: index, eventId: event.id, issues: eventIssues });
    }
  });
  
  if (issues.length > 0) {
    console.log(`  ✗ Found ${issues.length} events with issues:`);
    issues.forEach(({ eventIndex, eventId, issues: eventIssues }) => {
      console.log(`    Event ${eventIndex} (${eventId}):`);
      eventIssues.forEach(issue => console.log(`      - ${issue}`));
    });
    totalIssues += issues.length;
  } else {
    console.log(`  ✓ All ${events.length} events are valid`);
  }
});

console.log('\n=== Summary ===');
if (totalIssues === 0) {
  console.log('✓ All v3 JSON files are correctly formatted');
  console.log('✓ No unwanted flat fields found');
  console.log('✓ All required nested structures are present');
} else {
  console.log(`✗ Found issues in ${totalIssues} events across ${files.length} files`);
}

process.exit(totalIssues > 0 ? 1 : 0);
