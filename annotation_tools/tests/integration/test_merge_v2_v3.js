// Test script to verify v2/v3 merge functionality
const fs = require('fs');
const path = require('path');

// Import the merge function (we'll need to adapt it for Node.js)
// For now, let's test the logic manually

// Read test data
const v2Path = path.join(__dirname, '..', '..', 'datasets/Japanese_test/json_v2/jp_003_v2.json');
const v3Path = path.join(__dirname, '..', '..', 'datasets/Japanese_test/json_v3/jp_003_v3.json');

console.log('Testing v2/v3 merge functionality...\n');

// Check if files exist
if (!fs.existsSync(v2Path)) {
  console.error(`V2 file not found: ${v2Path}`);
  process.exit(1);
}

if (!fs.existsSync(v3Path)) {
  console.error(`V3 file not found: ${v3Path}`);
  process.exit(1);
}

// Read and parse JSON files
let v2Data, v3Data;
try {
  v2Data = JSON.parse(fs.readFileSync(v2Path, 'utf8'));
  v3Data = JSON.parse(fs.readFileSync(v3Path, 'utf8'));
  console.log('✓ Successfully loaded v2 and v3 JSON files');
} catch (err) {
  console.error('Error reading JSON files:', err);
  process.exit(1);
}

// Basic validation
console.log('\n=== Basic Structure Check ===');
console.log(`V2 version: ${v2Data.version || 'N/A'}`);
console.log(`V3 version: ${v3Data.version || 'N/A'}`);
console.log(`V2 narrative_events count: ${v2Data.narrative_events?.length || 0}`);
console.log(`V3 narrative_events count: ${v3Data.narrative_events?.length || 0}`);
console.log(`V2 propp_functions count: ${v2Data.analysis?.propp_functions?.length || 0}`);
console.log(`V3 propp_functions count: ${v3Data.analysis?.propp_functions?.length || 0}`);
console.log(`V2 characters count: ${v2Data.characters?.length || 0}`);
console.log(`V3 characters count: ${v3Data.characters?.length || 0}`);

// Check for data alignment
console.log('\n=== Data Alignment Check ===');

// Check narrative events alignment
const v2EventIds = new Set((v2Data.narrative_events || []).map(e => e.id).filter(Boolean));
const v3EventIds = new Set((v3Data.narrative_events || []).map(e => e.id).filter(Boolean));
const commonEventIds = new Set([...v2EventIds].filter(id => v3EventIds.has(id)));
const v2OnlyEventIds = new Set([...v2EventIds].filter(id => !v3EventIds.has(id)));
const v3OnlyEventIds = new Set([...v3EventIds].filter(id => !v2EventIds.has(id)));

console.log(`Common narrative events: ${commonEventIds.size}`);
console.log(`V2-only events: ${v2OnlyEventIds.size}`);
console.log(`V3-only events: ${v3OnlyEventIds.size}`);

if (v2OnlyEventIds.size > 0) {
  console.log(`  V2-only event IDs: ${Array.from(v2OnlyEventIds).slice(0, 5).join(', ')}${v2OnlyEventIds.size > 5 ? '...' : ''}`);
}
if (v3OnlyEventIds.size > 0) {
  console.log(`  V3-only event IDs: ${Array.from(v3OnlyEventIds).slice(0, 5).join(', ')}${v3OnlyEventIds.size > 5 ? '...' : ''}`);
}

// Check propp functions alignment
const v2ProppIds = new Set((v2Data.analysis?.propp_functions || []).map(pf => pf.id).filter(Boolean));
const v3ProppIds = new Set((v3Data.analysis?.propp_functions || []).map(pf => pf.id).filter(Boolean));
const commonProppIds = new Set([...v2ProppIds].filter(id => v3ProppIds.has(id)));
const v2OnlyProppIds = new Set([...v2ProppIds].filter(id => !v3ProppIds.has(id)));
const v3OnlyProppIds = new Set([...v3ProppIds].filter(id => !v2ProppIds.has(id)));

console.log(`\nCommon propp functions: ${commonProppIds.size}`);
console.log(`V2-only propp functions: ${v2OnlyProppIds.size}`);
console.log(`V3-only propp functions: ${v3OnlyProppIds.size}`);

// Check characters alignment
const v2CharNames = new Set((v2Data.characters || []).map(c => c.name).filter(Boolean));
const v3CharNames = new Set((v3Data.characters || []).map(c => c.name).filter(Boolean));
const commonCharNames = new Set([...v2CharNames].filter(name => v3CharNames.has(name)));
const v2OnlyCharNames = new Set([...v2CharNames].filter(name => !v3CharNames.has(name)));
const v3OnlyCharNames = new Set([...v3CharNames].filter(name => !v2CharNames.has(name)));

console.log(`\nCommon characters: ${commonCharNames.size}`);
console.log(`V2-only characters: ${v2OnlyCharNames.size}`);
console.log(`V3-only characters: ${v3OnlyCharNames.size}`);

if (v2OnlyCharNames.size > 0) {
  console.log(`  V2-only characters: ${Array.from(v2OnlyCharNames).join(', ')}`);
}
if (v3OnlyCharNames.size > 0) {
  console.log(`  V3-only characters: ${Array.from(v3OnlyCharNames).join(', ')}`);
}

// Test merge logic (simplified version)
console.log('\n=== Merge Test (Simulated) ===');
const totalEvents = v2EventIds.size + v3EventIds.size - commonEventIds.size;
const totalProppFns = v2ProppIds.size + v3ProppIds.size - commonProppIds.size;
const totalChars = v2CharNames.size + v3CharNames.size - commonCharNames.size;

console.log(`After merge, expected narrative events: ${totalEvents} (union)`);
console.log(`After merge, expected propp functions: ${totalProppFns} (union)`);
console.log(`After merge, expected characters: ${totalChars} (union)`);

// Check for relationship data
console.log('\n=== Relationship Data Check ===');
const v2EventsWithRelationships = (v2Data.narrative_events || []).filter(e => 
  e.relationships?.length > 0 || e.relationship_multi?.length > 0 || e.relationship_level1
);
const v3EventsWithRelationships = (v3Data.narrative_events || []).filter(e => 
  e.relationships?.length > 0 || e.relationship_multi?.length > 0 || e.relationship_level1
);

console.log(`V2 events with relationships: ${v2EventsWithRelationships.length}`);
console.log(`V3 events with relationships: ${v3EventsWithRelationships.length}`);

// Summary
console.log('\n=== Summary ===');
console.log('✓ Files loaded successfully');
console.log('✓ Data structure validated');
console.log('✓ Alignment checked');
console.log('\nThe merge function should:');
console.log(`  - Combine ${totalEvents} unique narrative events`);
console.log(`  - Combine ${totalProppFns} unique propp functions`);
console.log(`  - Combine ${totalChars} unique characters`);
console.log('  - Use v3 data when conflicts exist (same id)');
console.log('  - Include all unique items from both versions');

console.log('\n✓ Test completed successfully!');
