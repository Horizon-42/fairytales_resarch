// Fix v3 JSON files that have null agents/targets
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PROJECT_ROOT = path.resolve(__dirname, '..', '..');

console.log('=== Fixing v3 JSON Files ===\n');

const testDir = path.join(PROJECT_ROOT, '..', 'datasets/Japanese_test/json_v3');
const files = fs.readdirSync(testDir).filter(f => f.endsWith('.json'));

let fixedCount = 0;
let totalFixed = 0;

files.forEach(file => {
  const filePath = path.join(testDir, file);
  const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
  
  let fileFixed = false;
  const events = data.narrative_events || [];
  
  events.forEach((event, index) => {
    let eventFixed = false;
    
    // Fix null or non-array agents
    if (!Array.isArray(event.agents)) {
      event.agents = [];
      eventFixed = true;
    }
    
    // Fix null or non-array targets
    if (!Array.isArray(event.targets)) {
      event.targets = [];
      eventFixed = true;
    }
    
    if (eventFixed) {
      fileFixed = true;
      totalFixed++;
      console.log(`  Fixed event ${index} (${event.id || 'NO ID'}) in ${file}`);
    }
  });
  
  if (fileFixed) {
    // Write back the fixed file
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf8');
    fixedCount++;
    console.log(`✓ Fixed ${file}\n`);
  }
});

console.log(`=== Summary ===`);
console.log(`Files fixed: ${fixedCount}/${files.length}`);
console.log(`Events fixed: ${totalFixed}`);
if (fixedCount > 0) {
  console.log(`\n✓ Fixed JSON files have been saved`);
} else {
  console.log(`\n✓ No files needed fixing`);
}
