import React from "react";
import CreatableSelect from 'react-select/creatable';
import { PROPP_FUNCTIONS, TARGET_CATEGORIES, OBJECT_TYPES } from "../constants.js";
import { RELATIONSHIP_LEVEL1, RELATIONSHIP_LEVEL2, getRelationshipLevel2Options } from "../relationship_constants.js";
import { SENTIMENT_TAGS, SENTIMENT_DATA, getSentimentByTag } from "../sentiment_constants.js";
import { ACTION_CATEGORIES, ACTION_TYPES, ACTION_STATUS, getActionTypesForCategory, getContextTagsForAction } from "../action_taxonomy_constants.js";
import { generateUUID } from "../utils/fileHandler.js";
import { customSelectStyles } from "../utils/helpers.js";

// Map Propp function codes to full display names from CSV
const PROPP_FUNCTION_DISPLAY_NAMES = {
  "ABSENTATION": "Absentation",
  "INTERDICTION": "Interdiction",
  "VIOLATION": "Violation",
  "RECONNAISSANCE": "Reconnaissance",
  "DELIVERY": "Delivery",
  "TRICKERY": "Trickery",
  "COMPLICITY": "Complicity",
  "VILLAINY": "Villainy",
  "LACK": "Lack",
  "MEDIATION": "Meditation",
  "BEGINNING_COUNTERACTION": "Beginning counteraction",
  "DEPARTURE": "Departure",
  "FIRST_FUNCTION_DONOR": "First function of the Donor",
  "HERO_REACTION": "The hero's reaction",
  "RECEIPT_OF_AGENT": "Provision of a magical agent",
  "GUIDANCE": "Guidance",
  "STRUGGLE": "Struggle",
  "BRANDING": "Branding",
  "VICTORY": "Victory",
  "LIQUIDATION": "Liquidation of Lack",
  "RETURN": "Return",
  "PURSUIT": "Pursuit",
  "RESCUE": "Rescue",
  "UNRECOGNIZED_ARRIVAL": "Unrecognized arrival",
  "UNFOUNDED_CLAIMS": "Unfounded claims",
  "DIFFICULT_TASK": "Difficult task",
  "SOLUTION": "Solution",
  "RECOGNITION": "Recognised",
  "EXPOSURE": "Exposure",
  "TRANSFIGURATION": "Transfiguration",
  "PUNISHMENT": "Punishment",
  "WEDDING": "Wedding"
};

// Format Propp function name for display
const formatProppFunctionName = (fn) => {
  if (!fn) return fn;
  // Use mapping if available, otherwise fallback to title case conversion
  return PROPP_FUNCTION_DISPLAY_NAMES[fn] || fn
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
};

export default function NarrativeSection({
  narrativeStructure,
  setNarrativeStructure,
  crossValidation,
  setCrossValidation,
  motif,
  currentSelection,
  onAddProppFn,
  highlightedRanges,
  setHighlightedRanges
}) {
  const [sortByTimeOrder, setSortByTimeOrder] = React.useState(false);

  const charactersList = Array.isArray(motif.character_archetypes)
    ? motif.character_archetypes
    : [];
  
  const characterOptions = charactersList
    .map((c) => {
      if (typeof c === "string") return { label: c, value: c };
      const name = c.name || "Unnamed";
      const role = c.archetype || "Unknown";
      return { label: `${name} (${role})`, value: name };
    })
    .filter((o) => o.value && o.value !== "Unnamed");

  // Calculate max time_order to auto-assign for new items
  const maxTimeOrder = Math.max(
    0,
    ...narrativeStructure
      .filter(n => typeof n === "object" && n.time_order != null)
      .map(n => n.time_order || 0)
  );

  let items = narrativeStructure.map((item, index) => {
    if (typeof item === "string") {
      return {
        id: generateUUID(),
        event_type: "OTHER",
        description: item,
        agents: [],
        targets: [],
        text_span: null,
        target_type: "character",
        object_type: "",
        instrument: "",
        time_order: maxTimeOrder + 1 + index,
        relationship_level1: "",
        relationship_level2: "",
        sentiment: "",
        action_category: "",
        action_type: "",
        action_context: "",
        action_status: ""
      };
    }
    if (!item.id) {
      return {
        ...item,
        id: generateUUID(),
        time_order: item.time_order ?? (maxTimeOrder + 1 + index),
        relationship_level1: item.relationship_level1 || "",
        relationship_level2: item.relationship_level2 || "",
        sentiment: item.sentiment || "",
        action_category: item.action_category || (item.action_layer?.category || ""),
        action_type: item.action_type || (item.action_layer?.type || ""),
        action_context: item.action_context || (item.action_layer?.context || ""),
        action_status: item.action_status || (item.action_layer?.status || "")
      };
    }
    return {
      ...item,
      time_order: item.time_order ?? (maxTimeOrder + 1 + index),
      relationship_level1: item.relationship_level1 || "",
      relationship_level2: item.relationship_level2 || "",
      sentiment: item.sentiment || ""
    };
  });

  // Sort items
  if (sortByTimeOrder) {
    // Sort by time_order, with items without time_order at the end
    items = items.sort((a, b) => {
      const orderA = a.time_order ?? Infinity;
      const orderB = b.time_order ?? Infinity;
      return orderA - orderB;
    });
  } else {
    // Default: sort by text_span start position, with items without text_span at the end
    items = items.sort((a, b) => {
      const startA = a.text_span?.start ?? Infinity;
      const startB = b.text_span?.start ?? Infinity;
      return startA - startB;
    });
  }

  // Check if all items with text_span are highlighted
  const allHighlighted = React.useMemo(() => {
    if (!highlightedRanges) return false;
    const itemsWithSpan = items.filter(item => item.text_span);
    if (itemsWithSpan.length === 0) return false;

    return itemsWithSpan.every((item, idx) => {
      const key = `narrative-${idx}`;
      return highlightedRanges[key];
    });
  }, [highlightedRanges, items]);

  const updateItem = (index, field, value) => {
    // Find the item by ID since items are sorted
    const itemToUpdate = items[index];
    if (!itemToUpdate || !itemToUpdate.id) {
      // Fallback to index if no ID
      const next = [...items];
      next[index] = { ...next[index], [field]: value };
      setNarrativeStructure(next);
      return;
    }

    // Find the original index in narrativeStructure by ID
    const originalIndex = narrativeStructure.findIndex(n => 
      typeof n === "object" && n.id === itemToUpdate.id
    );

    if (originalIndex === -1) {
      // If not found, update the sorted items array
      const next = [...items];
      next[index] = { ...next[index], [field]: value };
      setNarrativeStructure(next);
      return;
    }

    // Update the original structure
    const next = [...narrativeStructure];
    if (typeof next[originalIndex] === "object") {
      next[originalIndex] = { ...next[originalIndex], [field]: value };
    } else {
      // Convert string to object if needed
      next[originalIndex] = {
        id: generateUUID(),
        event_type: "OTHER",
        description: next[originalIndex],
        agents: [],
        targets: [],
        text_span: null,
        target_type: "character",
        object_type: "",
        instrument: "",
        time_order: maxTimeOrder + 1,
        relationship_level1: "",
        relationship_level2: "",
        sentiment: "",
        [field]: value
      };
    }
    setNarrativeStructure(next);

    if (onAddProppFn && field === "event_type") {
      const updatedItem = typeof next[originalIndex] === "object" ? next[originalIndex] : items[index];
      onAddProppFn(updatedItem);
    }
  };

  const addItem = () => {
    const nextOrder = maxTimeOrder + 1;
    setNarrativeStructure([
      ...items,
      {
        id: generateUUID(),
        event_type: "",
        description: "",
        agents: [],
        targets: [],
        text_span: null,
        target_type: "character",
        object_type: "",
        instrument: "",
        time_order: nextOrder,
        relationship_level1: "",
        relationship_level2: "",
        sentiment: ""
      }
    ]);
  };

  const removeItem = (index) => {
    // Find the item by ID since items are sorted
    const itemToRemove = items[index];
    if (!itemToRemove || !itemToRemove.id) {
      // Fallback to index if no ID
      const next = items.filter((_, i) => i !== index);
      setNarrativeStructure(next);
      return;
    }

    // Find and remove from original structure by ID
    const next = narrativeStructure.filter(n => {
      if (typeof n === "object" && n.id === itemToRemove.id) {
        return false;
      }
      return true;
    });
    setNarrativeStructure(next);
  };

  const captureSelection = (index) => {
    if (!currentSelection) return;
    updateItem(index, "text_span", currentSelection);
  };

  const toggleHighlight = (idx, span) => {
    if (!setHighlightedRanges || !span) return;
    const key = `narrative-${idx}`;

    setHighlightedRanges(prev => {
      const next = { ...prev };
      const isAdding = !next[key];
      
      if (next[key]) {
        delete next[key];
      } else {
        next[key] = {
          start: span.start,
          end: span.end,
          color: "#60a5fa" // Blue for narrative events
        };
      }
      
      // Scroll to highlight when adding (not removing)
      if (isAdding) {
        setTimeout(() => {
          const markId = `${key}-mark`;
          const el = document.getElementById(markId);
          if (el) {
            el.scrollIntoView({ behavior: "smooth", block: "center" });
          }
        }, 100);
      }
      
      return next;
    });
  };

  const isHighlighted = (idx) => {
    return highlightedRanges && !!highlightedRanges[`narrative-${idx}`];
  };

  const toggleHighlightAll = () => {
    if (!setHighlightedRanges) return;

    if (allHighlighted) {
      // Clear all highlights
      setHighlightedRanges(prev => {
        const next = { ...prev };
        items.forEach((item, idx) => {
          const key = `narrative-${idx}`;
          delete next[key];
        });
        return next;
      });
    } else {
      // Highlight all items with text_span
      setHighlightedRanges(prev => {
        const next = { ...prev };
        items.forEach((item, idx) => {
          if (item.text_span) {
            const key = `narrative-${idx}`;
            next[key] = {
              start: item.text_span.start,
              end: item.text_span.end,
              color: "#60a5fa" // Blue for narrative events
            };
          }
        });
        return next;
      });
    }
  };

  const handleMultiCharChange = (index, field, newValue) => {
    const values = newValue ? newValue.map(o => o.value) : [];
    updateItem(index, field, values);
  };

  const handleBiasChange = (field, value) => {
    setCrossValidation({
      ...crossValidation,
      bias_reflection: {
        ...crossValidation.bias_reflection,
        [field]: value
      }
    });
  };

  return (
    <section className="card">
      <h2>Narrative Events</h2>
      <div className="section-header-row">
        <span>Story Sequence</span>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <button
            type="button"
            className="ghost-btn"
            onClick={toggleHighlightAll}
            style={{
              fontSize: "0.85rem",
              padding: "0.4rem 0.8rem",
              backgroundColor: allHighlighted ? "#60a5fa" : undefined,
              color: allHighlighted ? "#fff" : undefined
            }}
          >
            {allHighlighted ? "✓ Hide All" : "Highlight All"}
          </button>
          <button
            type="button"
            className="ghost-btn"
            onClick={() => setSortByTimeOrder(!sortByTimeOrder)}
            style={{
              fontSize: "0.85rem",
              padding: "0.4rem 0.8rem",
              backgroundColor: sortByTimeOrder ? "#60a5fa" : undefined,
              color: sortByTimeOrder ? "#fff" : undefined
            }}
          >
            {sortByTimeOrder ? "✓ By Time Order" : "By Text Position"}
          </button>
        </div>
      </div>

      {items.map((item, idx) => (
        <div key={item.id || idx} className="propp-row">
          <div className="grid-2">
            <div>
              <label>Event Type (Propp)</label>
              <select
                value={item.event_type}
                onChange={(e) => updateItem(idx, "event_type", e.target.value)}
              >
                <option value="">– Select Event –</option>
                {PROPP_FUNCTIONS.map((fn) => (
                  <option key={fn} value={fn}>
                    {formatProppFunctionName(fn)}
                  </option>
                ))}
                <option value="OTHER">Other</option>
              </select>
            </div>
            <div>
              <label>Text Selection</label>
              <div style={{ display: "flex", gap: "0.5rem" }}>
                <input
                  value={
                    item.text_span
                      ? `${item.text_span.start}-${item.text_span.end}`
                      : "None"
                  }
                  readOnly
                  placeholder="No selection"
                  style={{ background: "#f3f4f6", marginBottom: 0, flex: 1 }}
                />
                <button
                  type="button"
                  className="primary-btn"
                  style={{ padding: "0.5rem", fontSize: "0.75rem", height: "34px", whiteSpace: "nowrap" }}
                  onClick={() => captureSelection(idx)}
                  disabled={!currentSelection}
                >
                  Capture
                </button>
                <button
                  type="button"
                  className={`ghost-btn ${isHighlighted(idx) ? "active-highlight" : ""}`}
                  style={{
                    padding: "0.5rem",
                    fontSize: "0.75rem",
                    height: "34px",
                    background: isHighlighted(idx) ? "#60a5fa" : undefined,
                    color: isHighlighted(idx) ? "#fff" : undefined,
                    fontWeight: isHighlighted(idx) ? "bold" : undefined,
                    whiteSpace: "nowrap"
                  }}
                  onClick={() => toggleHighlight(idx, item.text_span)}
                  disabled={!item.text_span}
                >
                  {isHighlighted(idx) ? "Hide" : "Highlight"}
                </button>
              </div>
            </div>
          </div>

          <label>
            Description / Detail
            <textarea
              rows={2}
              value={item.description}
              onChange={(e) => updateItem(idx, "description", e.target.value)}
              placeholder="Describe the specific event..."
            />
          </label>

          <div className="grid-2">
            <label>
              Agents (Doer)
              <CreatableSelect
                isMulti
                options={characterOptions}
                value={(item.agents || []).map(agentName => {
                  const found = characterOptions.find(opt => opt.value === agentName);
                  return found || { label: agentName, value: agentName };
                })}
                onChange={(newValue) => handleMultiCharChange(idx, "agents", newValue)}
                placeholder="Select or create agents..."
                styles={customSelectStyles}
              />
            </label>
            <label>
              Targets (Receiver)
              {item.target_type === "object" ? (
                <input
                  value={item.targets && item.targets.length > 0 ? item.targets[0] : ""}
                  onChange={(e) => updateItem(idx, "targets", [e.target.value])}
                  placeholder="Enter object target name..."
                  style={{ marginTop: '4px', width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
                />
              ) : (
                <CreatableSelect
                  isMulti
                  options={characterOptions}
                  value={(item.targets || []).map(targetName => {
                    const found = characterOptions.find(opt => opt.value === targetName);
                    return found || { label: targetName, value: targetName };
                  })}
                  onChange={(newValue) => handleMultiCharChange(idx, "targets", newValue)}
                  placeholder="Select or create targets..."
                  styles={customSelectStyles}
                />
              )}
            </label>
          </div>

          <div className="grid-3">
            <label>
              Target Type
              <select
                value={item.target_type || ""}
                onChange={(e) => updateItem(idx, "target_type", e.target.value)}
              >
                <option value="">– Select –</option>
                {TARGET_CATEGORIES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </label>
            {item.target_type === "object" && (
              <label>
                Object Type
                <select
                  value={item.object_type || ""}
                  onChange={(e) => updateItem(idx, "object_type", e.target.value)}
                >
                  <option value="">– Select –</option>
                  {OBJECT_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </label>
            )}
            <label>
              Instrument
              <input
                value={item.instrument || ""}
                onChange={(e) => updateItem(idx, "instrument", e.target.value)}
                placeholder="Instrument used..."
              />
            </label>
          </div>

          {item.target_type === "character" && (
            <div className="grid-3">
              <label>
                Relationship L1
                <select
                  value={item.relationship_level1 || ""}
                  onChange={(e) => {
                    updateItem(idx, "relationship_level1", e.target.value);
                    // Reset level2 when level1 changes (React will batch these updates)
                    if (item.relationship_level2) {
                      updateItem(idx, "relationship_level2", "");
                    }
                  }}
                >
                  <option value="">– Select –</option>
                  {RELATIONSHIP_LEVEL1.map((level1) => {
                    // Extract English part from format "中文(English)" or use as-is if no parentheses
                    const match = level1.match(/\(([^)]+)\)/);
                    const displayName = match ? match[1] : level1;
                    return (
                      <option key={level1} value={level1}>
                        {displayName}
                      </option>
                    );
                  })}
                </select>
              </label>
              <label>
                Relationship L2
                <select
                  value={item.relationship_level2 || ""}
                  onChange={(e) => updateItem(idx, "relationship_level2", e.target.value)}
                  disabled={!item.relationship_level1}
                >
                  <option value="">– Select –</option>
                  {item.relationship_level1 && getRelationshipLevel2Options(item.relationship_level1).map((level2) => (
                    <option key={level2.tag} value={level2.tag}>
                      {level2.tag}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Sentiment
                <select
                  value={item.sentiment || ""}
                  onChange={(e) => updateItem(idx, "sentiment", e.target.value)}
                >
                  <option value="">– Select –</option>
                  {SENTIMENT_TAGS.map((tag) => (
                    <option key={tag} value={tag}>
                      {tag}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          )}

          {item.target_type === "character" && (
            <div className="grid-3" style={{ marginTop: "0.5rem" }}>
              <label>
                Action Category
                <select
                  value={item.action_category || ""}
                  onChange={(e) => {
                    updateItem(idx, "action_category", e.target.value);
                    // Reset action_type and action_context when category changes
                    if (item.action_type) {
                      updateItem(idx, "action_type", "");
                    }
                    if (item.action_context) {
                      updateItem(idx, "action_context", "");
                    }
                  }}
                >
                  <option value="">– Select –</option>
                  {ACTION_CATEGORIES.map((cat) => (
                    <option key={cat.code} value={cat.code}>
                      {cat.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Action Type
                <select
                  value={item.action_type || ""}
                  onChange={(e) => {
                    updateItem(idx, "action_type", e.target.value);
                    // Reset context when action type changes
                    if (item.action_context) {
                      updateItem(idx, "action_context", "");
                    }
                  }}
                  disabled={!item.action_category}
                >
                  <option value="">– Select –</option>
                  {item.action_category && getActionTypesForCategory(item.action_category).map((action) => (
                    <option key={action.code} value={action.code}>
                      {action.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Action Status
                <select
                  value={item.action_status || ""}
                  onChange={(e) => updateItem(idx, "action_status", e.target.value)}
                >
                  <option value="">– Select –</option>
                  {ACTION_STATUS.map((status) => (
                    <option key={status.code} value={status.code}>
                      {status.name}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          )}

          {item.target_type === "character" && item.action_category && item.action_type && (
            <div style={{ marginTop: "0.5rem" }}>
              <label>
                Context (optional)
                <input
                  type="text"
                  value={item.action_context || ""}
                  onChange={(e) => updateItem(idx, "action_context", e.target.value)}
                  placeholder={`e.g., ${getContextTagsForAction(item.action_category, item.action_type).slice(0, 3).join(", ")}`}
                  list={`context-suggestions-${idx}`}
                />
                <datalist id={`context-suggestions-${idx}`}>
                  {getContextTagsForAction(item.action_category, item.action_type).map((tag) => (
                    <option key={tag} value={tag} />
                  ))}
                </datalist>
              </label>
            </div>
          )}
          
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginTop: "0.5rem" }}>
            <div style={{ display: "flex", alignItems: "baseline", gap: "0.25rem" }}>
              <span style={{ fontSize: "0.85rem", color: "#6b7280" }}>Time Order:</span>
              <input
                type="number"
                min="1"
                value={item.time_order ?? ""}
                onChange={(e) => updateItem(idx, "time_order", parseInt(e.target.value) || null)}
                style={{ 
                  width: "60px", 
                  padding: "0.4rem 0.5rem", 
                  fontSize: "0.8rem", 
                  border: "1px solid #cbd5e1",
                  borderRadius: "6px",
                  boxSizing: "border-box",
                  lineHeight: "1.2"
                }}
                placeholder="#"
              />
            </div>
            <button
              type="button"
              className="ghost-btn"
              style={{ color: "#ef4444", borderColor: "#ef4444" }}
              onClick={() => removeItem(idx)}
            >
              Remove Event
            </button>
          </div>
        </div>
      ))}

      <button type="button" className="ghost-btn" onClick={addItem} style={{ marginTop: "1rem" }}>
        + Add Event
      </button>

      <hr />

      <h3>Bias reflection</h3>
      <label>
        Cultural reading
        <textarea
          rows={2}
          value={crossValidation.bias_reflection.cultural_reading}
          onChange={(e) => handleBiasChange("cultural_reading", e.target.value)}
        />
      </label>
      <label>
        Gender norms
        <textarea
          rows={2}
          value={crossValidation.bias_reflection.gender_norms}
          onChange={(e) => handleBiasChange("gender_norms", e.target.value)}
        />
      </label>
    </section>
  );
}

