import { generateUUID } from './fileHandler.js';

// Helper function for multi-select
export function multiSelectFromEvent(e) {
  return Array.from(e.target.selectedOptions).map((o) => o.value);
}

// Download JSON file
export function downloadJson(filename, data) {
  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: "application/json"
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

// Convert relative path to dataset hint
export function relPathToDatasetHint(path) {
  const normalized = path.replace(/^(\.\/|\/)+/, "");
  return normalized;
}

// Distinct pastel-like colors for highlighting
export const HIGHLIGHT_COLORS = [
  "#fef08a", // yellow
  "#bbf7d0", // green
  "#bfdbfe", // blue
  "#fbcfe8", // pink
  "#ddd6fe", // indigo
  "#fed7aa", // orange
  "#99f6e4", // teal
  "#e9d5ff", // violet
  "#fecaca", // red-ish
  "#a5f3fc"  // cyan
];

// Extract English part from relationship level1 format "中文(English)" or return as-is
export function extractEnglishFromRelationship(relationshipValue) {
  if (!relationshipValue || typeof relationshipValue !== 'string') {
    return relationshipValue;
  }
  // Check if it matches the format "中文(English)"
  const match = relationshipValue.match(/\(([^)]+)\)/);
  if (match) {
    return match[1]; // Return English part
  }
  // If no parentheses, return as-is (might be custom value or already English)
  return relationshipValue;
}

// Factory for empty Propp function
export const emptyProppFn = () => ({
  id: generateUUID(),
  fn: "",
  spanType: "paragraph",
  span: { start: 0, end: 0 },
  textSpan: { start: 0, end: 0, text: "" },
  evidence: "",
  narrative_event_id: null
});

// Custom styles for react-select
export const customSelectStyles = {
  container: (base) => ({ ...base, marginTop: '4px' }),
  multiValueLabel: (base) => ({
    ...base,
    fontSize: '100%',
    padding: '2px 4px'
  }),
  multiValue: (base) => ({
    ...base,
    padding: '2px'
  })
};

