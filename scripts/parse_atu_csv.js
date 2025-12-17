const fs = require('fs');
const path = require('path');

// Read CSV file
const csvPath = path.join(__dirname, '..', 'ATU_types_complete.csv');
const csvContent = fs.readFileSync(csvPath, 'utf-8');

// Parse CSV
const lines = csvContent.trim().split('\n');
const headers = lines[0].split(',');

// Build hierarchical structure
const hierarchy = {};

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
    atu_number,
    title,
    level_1_category,
    level_2_category,
    level_3_category,
    category_range
  ] = fields;

  // Build hierarchy
  if (!hierarchy[level_1_category]) {
    hierarchy[level_1_category] = {};
  }

  if (!hierarchy[level_1_category][level_2_category]) {
    hierarchy[level_1_category][level_2_category] = {};
  }

  // level_3_category can be empty - use "general" as default
  const l3Key = level_3_category || 'general';
  if (!hierarchy[level_1_category][level_2_category][l3Key]) {
    hierarchy[level_1_category][level_2_category][l3Key] = [];
  }

  hierarchy[level_1_category][level_2_category][l3Key].push({
    number: atu_number,
    title: title,
    range: category_range
  });
}

// Convert to flat structure for easier use in React
const atuHierarchy = [];

// Level 1
Object.keys(hierarchy).forEach(level1 => {
  const level1Item = {
    level: 1,
    name: level1,
    key: level1,
    children: []
  };

  // Level 2
  Object.keys(hierarchy[level1]).forEach(level2 => {
    const level2Item = {
      level: 2,
      name: level2,
      key: `${level1}|${level2}`,
      parentKey: level1,
      children: []
    };

    // Level 3
    Object.keys(hierarchy[level1][level2]).forEach(level3 => {
      const level3Item = {
        level: 3,
        name: level3, // Now "general" instead of null when empty
        key: `${level1}|${level2}|${level3}`,
        parentKey: `${level1}|${level2}`,
        children: hierarchy[level1][level2][level3].map(item => ({
          level: 4,
          number: item.number,
          title: item.title,
          key: `ATU${item.number}`,
          parentKey: `${level1}|${level2}|${level3}`
        }))
      };
      level2Item.children.push(level3Item);
    });

    level1Item.children.push(level2Item);
  });

  atuHierarchy.push(level1Item);
});

// Generate JavaScript export
const jsContent = `// Auto-generated from ATU_types_complete.csv
// Structure: hierarchical ATU classification
export const ATU_HIERARCHY = ${JSON.stringify(atuHierarchy, null, 2)};

// Helper function to get all ATU items
export function getAllATUItems() {
  const items = [];
  function traverse(nodes) {
    nodes.forEach(node => {
      if (node.number) {
        items.push({
          number: node.number,
          title: node.title,
          key: node.key,
          level1: node.key.split('|')[0],
          level2: node.key.split('|')[1],
          level3: node.key.split('|')[2]
        });
      }
      if (node.children) {
        traverse(node.children);
      }
    });
  }
  traverse(ATU_HIERARCHY);
  return items;
}

// Helper function to find ATU by number
export function findATUByNumber(number) {
  const items = getAllATUItems();
  return items.find(item => item.number === number);
}
`;

// Write to constants file or separate file
const outputPath = path.join(__dirname, '..', 'annotation_tools', 'src', 'atu_hierarchy.js');
fs.writeFileSync(outputPath, jsContent, 'utf-8');

console.log(`Generated ATU hierarchy with ${atuHierarchy.length} level 1 categories`);
console.log(`Output written to: ${outputPath}`);
