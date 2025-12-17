const fs = require('fs');
const path = require('path');

// Read CSV file
const csvPath = path.join(__dirname, '..', 'Motif', 'Motifs_level1_3.csv');
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
    motif_code,
    title,
    level_1_category,
    level_2_category,
    level_2_range,
    level_3_category,
    level_3_range
  ] = fields;

  // Skip if essential fields are empty
  if (!motif_code || !level_1_category || !level_2_category) continue;

  // Build hierarchy
  if (!hierarchy[level_1_category.trim()]) {
    hierarchy[level_1_category.trim()] = {};
  }

  const l2Key = level_2_category.trim();
  const l2Range = level_2_range ? level_2_range.trim() : '';
  if (!hierarchy[level_1_category.trim()][l2Key]) {
    hierarchy[level_1_category.trim()][l2Key] = {
      range: l2Range,
      level3: {}
    };
  }

  // Level 3 category (may be empty)
  const l3Key = (level_3_category && level_3_category.trim()) ? level_3_category.trim() : 'general';
  const l3Range = level_3_range ? level_3_range.trim() : '';

  if (!hierarchy[level_1_category.trim()][l2Key].level3[l3Key]) {
    hierarchy[level_1_category.trim()][l2Key].level3[l3Key] = {
      range: l3Range,
      items: []
    };
  }

  hierarchy[level_1_category.trim()][l2Key].level3[l3Key].items.push({
    code: motif_code.trim(),
    title: title ? title.trim() : ''
  });
}

// Convert to hierarchical structure for React
const motifHierarchy = [];

Object.keys(hierarchy).forEach(level1 => {
  const level1Item = {
    level: 1,
    name: level1,
    key: level1,
    children: []
  };

  Object.keys(hierarchy[level1]).forEach(level2 => {
    const l2Data = hierarchy[level1][level2];
    const level2Item = {
      level: 2,
      name: level2,
      range: l2Data.range,
      key: `${level1}|${level2}`,
      parentKey: level1,
      children: []
    };

    Object.keys(l2Data.level3).forEach(level3 => {
      const l3Data = l2Data.level3[level3];
      const level3Item = {
        level: 3,
        name: level3 === 'general' ? null : level3,
        range: l3Data.range,
        key: `${level1}|${level2}|${level3}`,
        parentKey: `${level1}|${level2}`,
        children: l3Data.items.map(item => ({
          level: 4,
          code: item.code,
          title: item.title,
          key: item.code,
          parentKey: `${level1}|${level2}|${level3}`
        }))
      };
      level2Item.children.push(level3Item);
    });

    level1Item.children.push(level2Item);
  });

  motifHierarchy.push(level1Item);
});

// Generate JavaScript export
const jsContent = `// Auto-generated from Motifs_level1_3.csv
// Structure: hierarchical Motif classification (Level 1-4)
export const MOTIF_HIERARCHY_LEVEL1_3 = ${JSON.stringify(motifHierarchy, null, 2)};

// Helper function to get all motif items
export function getAllMotifItemsLevel1_3() {
  const items = [];
  function traverse(nodes) {
    nodes.forEach(node => {
      if (node.code) {
        items.push({
          code: node.code,
          title: node.title,
          key: node.key,
          level: node.level
        });
      }
      if (node.children) {
        traverse(node.children);
      }
    });
  }
  traverse(MOTIF_HIERARCHY_LEVEL1_3);
  return items;
}

// Helper function to find motif by code
export function findMotifByCodeLevel1_3(code) {
  const items = getAllMotifItemsLevel1_3();
  return items.find(item => item.code === code);
}
`;

// Write to file
const outputPath = path.join(__dirname, '..', 'annotation_tools', 'src', 'motif_hierarchy_level1_3.js');
fs.writeFileSync(outputPath, jsContent, 'utf-8');

console.log(`Generated Motif hierarchy (Level 1-3 CSV) with ${motifHierarchy.length} level 1 categories`);
console.log(`Output written to: ${outputPath}`);
