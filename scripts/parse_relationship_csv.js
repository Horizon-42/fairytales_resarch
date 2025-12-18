const fs = require('fs');
const path = require('path');

// Read the CSV file
const csvPath = path.join(__dirname, '../Character_Resources/relationship.csv');
const csvContent = fs.readFileSync(csvPath, 'utf-8');

const lines = csvContent.split('\n').filter(line => line.trim());
const headers = lines[0].split(',');

// Parse relationship data with two levels
const relationshipData = {};
let currentLevel1 = null;

for (let i = 1; i < lines.length; i++) {
  const line = lines[i];
  const parts = line.split(',');
  
  const level1 = parts[0]?.trim();
  const level2Tag = parts[1]?.trim();
  const definition = parts[2]?.trim();
  const context = parts[3]?.trim();
  
  if (level1 && level1 !== '') {
    currentLevel1 = level1;
    if (!relationshipData[currentLevel1]) {
      relationshipData[currentLevel1] = [];
    }
  }
  
  if (level2Tag && currentLevel1) {
    relationshipData[currentLevel1].push({
      tag: level2Tag,
      definition: definition || '',
      context: context || ''
    });
  }
}

// Generate JavaScript export
const jsContent = `// Relationship categories with two-level structure
// Generated from Character_Resources/relationship.csv

export const RELATIONSHIP_LEVEL1 = ${JSON.stringify(Object.keys(relationshipData), null, 2)};

export const RELATIONSHIP_LEVEL2 = ${JSON.stringify(relationshipData, null, 2)};

// Helper function to get level 2 options for a given level 1
export function getRelationshipLevel2Options(level1) {
  return RELATIONSHIP_LEVEL2[level1] || [];
}
`;

const outputPath = path.join(__dirname, '../annotation_tools/src/relationship_constants.js');
fs.writeFileSync(outputPath, jsContent, 'utf-8');

console.log('Relationship constants generated successfully!');
console.log('Level 1 categories:', Object.keys(relationshipData));
