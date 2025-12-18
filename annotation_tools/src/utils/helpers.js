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

// Build action_layer object from individual action fields
export function buildActionLayer(narrativeItem) {
  if (!narrativeItem) return undefined;

  const category = narrativeItem.action_category || narrativeItem.action_layer?.category;
  const type = narrativeItem.action_type || narrativeItem.action_layer?.type;
  const status = narrativeItem.action_status || narrativeItem.action_layer?.status;

  // Only create action_layer if we have at least category, type, and status
  if (!category || !type || !status) {
    return undefined;
  }

  const actionLayer = {
    category: category,
    type: type,
    status: status
  };

  // Add context if provided
  const context = narrativeItem.action_context || narrativeItem.action_layer?.context;
  if (context && context.trim()) {
    actionLayer.context = context.trim();
  }

  return actionLayer;
}

// Extract action fields from action_layer object (for backward compatibility)
export function extractActionFields(narrativeItem) {
  if (!narrativeItem) return {};

  // If action_layer exists, extract fields from it
  if (narrativeItem.action_layer) {
    return {
      action_category: narrativeItem.action_layer.category || "",
      action_type: narrativeItem.action_layer.type || "",
      action_context: narrativeItem.action_layer.context || "",
      action_status: narrativeItem.action_layer.status || ""
    };
  }

  // Otherwise return existing fields or empty strings
  return {
    action_category: narrativeItem.action_category || "",
    action_type: narrativeItem.action_type || "",
    action_context: narrativeItem.action_context || "",
    action_status: narrativeItem.action_status || ""
  };
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

