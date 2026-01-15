// Test that v3 JSON files don't contain relationship_multi
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PROJECT_ROOT = path.resolve(__dirname, '..', '..');

console.log('=== Testing V3 JSON Files for relationship_multi ===\n');

const testDir = path.join(PROJECT_ROOT, '..', 'datasets/Japanese_test/json_v3');
const files = fs.readdirSync(testDir).filter(f => f.endsWith('.json'));

let foundIssues = false;

files.forEach(file => {
  const filePath = path.join(testDir, file);
  const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
  
  const events = data.narrative_events || [];
  const issues = [];
  
  events.forEach((event, index) => {
    if ('relationship_multi' in event) {
      issues.push(`Event ${index} (${event.id || 'NO ID'}): Has relationship_multi field`);
      foundIssues = true;
    }
  });
  
  if (issues.length > 0) {
    console.log(`✗ ${file}:`);
    issues.forEach(issue => console.log(`  - ${issue}`));
  }
});

if (!foundIssues) {
  console.log(`✓ All ${files.length} v3 JSON files are clean (no relationship_multi field)`);
} else {
  console.log(`\n✗ Found relationship_multi in some files - this should not be saved in v3!`);
}

process.exit(foundIssues ? 1 : 0);
