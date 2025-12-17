const fs = require('fs');
const path = require('path');

// Read CSV file
const csvPath = path.join(__dirname, '..', 'Motifs_complete.csv');
const csvContent = fs.readFileSync(csvPath, 'utf-8');

// Parse CSV
const lines = csvContent.trim().split('\n');
const headers = lines[0].split(',');

// Build a map of all items by code
const itemsByCode = {};
const rootItems = [];

for (let i = 1; i < lines.length; i++) {
  // Parse CSV line (handling quoted fields)
  const line = lines[i];
  const fields = [];
  let current = '';
  let inQuotes = false;
  
  for (let j = 0; j < line.length; j++) {
    const char = line[j];
    if (char === '"') {
      if (line[j + 1] === '"') {
        current += '"';
        j++;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (char === ',' && !inQuotes) {
      fields.push(current);
      current = '';
    } else {
      current += char;
    }
  }
  fields.push(current);

  const [
    code,
    level,
    parentCode,
    description,
    source,
    lineNumber
  ] = fields;

  // Skip if code is empty
  if (!code || !code.trim()) continue;

  const item = {
    code: code.trim(),
    level: parseInt(level) || 1,
    parentCode: parentCode ? parentCode.trim() : null,
    description: description || '',
    source: source || '',
    lineNumber: lineNumber || '',
    children: []
  };

  itemsByCode[item.code] = item;

  if (!item.parentCode || item.parentCode === '') {
    rootItems.push(item);
  }
}

// Build hierarchy by linking children to parents
Object.values(itemsByCode).forEach(item => {
  if (item.parentCode && itemsByCode[item.parentCode]) {
    itemsByCode[item.parentCode].children.push(item);
  }
});

// Sort children by code for consistent ordering
function sortChildrenRecursive(item) {
  item.children.sort((a, b) => a.code.localeCompare(b.code));
  item.children.forEach(child => sortChildrenRecursive(child));
}

rootItems.forEach(item => sortChildrenRecursive(item));

// Convert to hierarchical structure for React
function convertToHierarchy(items) {
  return items.map(item => ({
    level: item.level,
    code: item.code,
    description: item.description,
    key: item.code,
    children: item.children.length > 0 ? convertToHierarchy(item.children) : []
  }));
}

const motifHierarchy = convertToHierarchy(rootItems);

// Generate JavaScript export
const jsContent = `// Auto-generated from Motifs_complete.csv
// Structure: hierarchical Motif classification
export const MOTIF_HIERARCHY = ${JSON.stringify(motifHierarchy, null, 2)};

// Helper function to get all motif items
export function getAllMotifItems() {
  const items = [];
  function traverse(nodes) {
    nodes.forEach(node => {
      items.push({
        code: node.code,
        description: node.description,
        key: node.key,
        level: node.level
      });
      if (node.children) {
        traverse(node.children);
      }
    });
  }
  traverse(MOTIF_HIERARCHY);
  return items;
}

// Helper function to find motif by code
export function findMotifByCode(code) {
  const items = getAllMotifItems();
  return items.find(item => item.code === code);
}
`;

// Write to file
const outputPath = path.join(__dirname, '..', 'annotation_tools', 'src', 'motif_hierarchy.js');
fs.writeFileSync(outputPath, jsContent, 'utf-8');

console.log(`Generated Motif hierarchy with ${rootItems.length} root items`);
console.log(`Output written to: ${outputPath}`);
console.log(`Total items processed: ${Object.keys(itemsByCode).length}`);
