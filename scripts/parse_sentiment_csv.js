const fs = require('fs');
const path = require('path');

// Read the CSV file
const csvPath = path.join(__dirname, '../Character_Resources/sentiment.csv');
const csvContent = fs.readFileSync(csvPath, 'utf-8');

const lines = csvContent.split('\n').filter(line => line.trim());
const headers = lines[0].split(',');

// Parse sentiment data
const sentiments = [];

for (let i = 1; i < lines.length; i++) {
  const line = lines[i];
  const parts = line.split(',');
  
  const tag = parts[0]?.trim();
  const chineseName = parts[1]?.trim();
  const polarity = parts[2]?.trim();
  const behavior = parts[3]?.trim();
  
  if (tag) {
    sentiments.push({
      tag: tag,
      chineseName: chineseName || '',
      polarity: polarity || '',
      behavior: behavior || ''
    });
  }
}

// Generate JavaScript export
const jsContent = `// Sentiment tags
// Generated from Character_Resources/sentiment.csv

export const SENTIMENT_TAGS = ${JSON.stringify(sentiments.map(s => s.tag), null, 2)};

export const SENTIMENT_DATA = ${JSON.stringify(sentiments, null, 2)};

// Helper function to get sentiment by tag
export function getSentimentByTag(tag) {
  return SENTIMENT_DATA.find(s => s.tag === tag);
}
`;

const outputPath = path.join(__dirname, '../annotation_tools/src/sentiment_constants.js');
fs.writeFileSync(outputPath, jsContent, 'utf-8');

console.log('Sentiment constants generated successfully!');
console.log('Sentiment tags:', sentiments.map(s => s.tag));
