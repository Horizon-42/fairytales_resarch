import React from "react";
import CreatableSelect from 'react-select/creatable';
import { PROPP_FUNCTIONS, TARGET_CATEGORIES, OBJECT_TYPES } from "../constants.js";
import { RELATIONSHIP_LEVEL1, RELATIONSHIP_LEVEL2, getRelationshipLevel2Options } from "../relationship_constants.js";
import { SENTIMENT_TAGS, SENTIMENT_DATA, getSentimentByTag } from "../sentiment_constants.js";
import { ACTION_CATEGORIES, ACTION_TYPES, ACTION_STATUS, NARRATIVE_FUNCTIONS, getActionTypesForCategory, getContextTagsForAction } from "../action_taxonomy_constants.js";
import { generateUUID } from "../utils/fileHandler.js";
import { customSelectStyles } from "../utils/helpers.js";
import {
  ensureRelationshipMultiEntryShape,
  buildMultiCharUpdatesWithEndpointSync,
  deriveRelationshipUiState,
  ensureAtLeastOneRelationshipMulti,
  computeMaxTimeOrder,
  buildNarrativeItems,
  sortNarrativeItemsInPlace,
  removeNarrativeEntryById,
  applyNarrativeItemUpdate,
  toggleNarrativeHighlightMap,
  toggleAllNarrativeHighlightsMap,
  computeAllNarrativeHighlighted,
  narrativeHighlightKey,
  narrativeHighlightMarkIdFromKey,
  updateRelationshipMultiRow,
  addRelationshipMultiRow,
  removeRelationshipMultiRow,
  buildSetRelationshipMultiUpdates,
} from "./narrativeSectionLogic.js";

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
  setHighlightedRanges,
  onAutoSegmentNarratives,
  autoSegmentNarrativesLoading,
  onAutoAnnotateEvent,
  autoAnnotateEventLoading
}) {
  const [sortByTimeOrder, setSortByTimeOrder] = React.useState(false);
  const [autoSegmentMode, setAutoSegmentMode] = React.useState("embedding_assisted");
  // State for annotation mode and additional prompt for each event
  const [eventAnnotationModes, setEventAnnotationModes] = React.useState({});
  const [eventAdditionalPrompts, setEventAdditionalPrompts] = React.useState({});

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
  const maxTimeOrder = computeMaxTimeOrder(narrativeStructure);

  let items = buildNarrativeItems({
    narrativeStructure,
    maxTimeOrder,
    uuidFn: generateUUID
  });

  sortNarrativeItemsInPlace(items, sortByTimeOrder);

  // Check if all items with text_span are highlighted
  const allHighlighted = React.useMemo(() => {
    return computeAllNarrativeHighlighted({ highlightedRanges, items });
  }, [highlightedRanges, items]);

  const updateItem = (index, fieldOrUpdates, value) => {
    // Support both single field update (field, value) and batch update (updates object)
    const updates = typeof fieldOrUpdates === 'string'
      ? { [fieldOrUpdates]: value }
      : fieldOrUpdates;

    const next = applyNarrativeItemUpdate({
      items,
      narrativeStructure,
      index,
      updates,
      uuidFn: generateUUID,
      maxTimeOrder
    });
    setNarrativeStructure(next);

    // Intentionally left as-is: onAddProppFn behavior is preserved elsewhere.
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
        relationship_multi: [],
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
    const next = removeNarrativeEntryById(narrativeStructure, itemToRemove.id);
    setNarrativeStructure(next);
  };

  const captureSelection = (index) => {
    if (!currentSelection) return;
    updateItem(index, "text_span", currentSelection);
  };

  const toggleHighlight = (idx, span) => {
    if (!setHighlightedRanges || !span) return;

    setHighlightedRanges((prev) => {
      const { next, isAdding, key } = toggleNarrativeHighlightMap(prev, { idx, span, color: "#60a5fa" });

      if (isAdding) {
        const scrollToMark = (highlightKey) => {
          const markId = narrativeHighlightMarkIdFromKey(highlightKey);
          const el = document.getElementById(markId);
          if (el) el.scrollIntoView({ behavior: "smooth", block: "center" });
        };

        setTimeout(() => scrollToMark(key), 100);
      }

      return next;
    });
  };

  const isHighlighted = (idx) => {
    return highlightedRanges && !!highlightedRanges[narrativeHighlightKey(idx)];
  };

  const toggleHighlightAll = () => {
    if (!setHighlightedRanges) return;

    setHighlightedRanges((prev) =>
      toggleAllNarrativeHighlightsMap(prev, { items, allHighlighted, color: "#60a5fa" })
    );
  };

  const handleMultiCharChange = (index, field, newValue) => {
    const values = newValue ? newValue.map(o => o.value) : [];
    const item = items[index];
    const updates = buildMultiCharUpdatesWithEndpointSync({ item, field, values });
    updateItem(index, updates);
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

  const renderRelationshipLevel1Options = () =>
    RELATIONSHIP_LEVEL1.map((level1) => (
      <option key={level1} value={level1}>
        {level1}
      </option>
    ));

  const renderRelationshipLevel2Options = (level1) =>
    (level1 ? getRelationshipLevel2Options(level1) : []).map((level2) => (
      <option key={level2.tag} value={level2.tag}>
        {level2.tag}
      </option>
    ));

  const relationshipRowControlStyle = {
    height: "32px",
    fontSize: "0.85rem",
    padding: "0.3rem 0.45rem",
    lineHeight: "1.2",
    marginBottom: 0,
    boxSizing: "border-box"
  };

  const renderMultiRelationshipEditor = ({
    agents,
    targets,
    ensureAtLeastOneRelationship,
    setRelationshipMultiList
  }) => {
    return (
      <div style={{ marginBottom: "0.25rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: "0.5rem" }}>
          <div style={{ fontSize: "0.8rem", color: "#6b7280" }}>
            Relationship (multi)
          </div>
          <button
            type="button"
            className="ghost-btn"
            onClick={() => {
              const current = ensureAtLeastOneRelationship();
              setRelationshipMultiList(addRelationshipMultiRow(current, { agents, targets }));
            }}
            style={{ padding: "0.2rem 0.45rem", height: "28px", fontSize: "0.8rem" }}
          >
            + Add
          </button>
        </div>

        {ensureAtLeastOneRelationship().map((rel, relIdx) => {
          const relEntry = ensureRelationshipMultiEntryShape(rel);
          const level1 = relEntry.relationship_level1 || "";

          const updateRel = (partial, resetLevel2 = false) => {
            const current = ensureAtLeastOneRelationship();
            setRelationshipMultiList(updateRelationshipMultiRow(current, relIdx, partial, resetLevel2));
          };

          return (
            <div
              key={relIdx}
              style={{
                display: "grid",
                gridTemplateColumns: "minmax(0, 1fr) minmax(0, 1.2fr) minmax(0, 1fr) minmax(0, 1fr) minmax(0, 1fr) auto",
                gap: "0.5rem",
                alignItems: "end",
                marginTop: "0.4rem"
              }}
            >
              <label style={{ marginBottom: 0, minWidth: 0 }}>
                Agent
                <select
                  value={agents.length === 1 ? (agents[0] || "") : relEntry.agent}
                  onChange={(e) => updateRel({ agent: e.target.value })}
                  disabled={agents.length <= 1}
                  style={relationshipRowControlStyle}
                  title={(agents.length === 1 ? agents[0] : relEntry.agent) || "Agent"}
                >
                  <option value="">– Select –</option>
                  {agents.map((name) => (
                    <option key={name} value={name}>
                      {name}
                    </option>
                  ))}
                </select>
              </label>

              <label style={{ marginBottom: 0, minWidth: 0 }}>
                Relationship L1
                <select
                  value={relEntry.relationship_level1}
                  onChange={(e) => updateRel({ relationship_level1: e.target.value }, true)}
                  style={relationshipRowControlStyle}
                  title={relEntry.relationship_level1 || "Relationship L1"}
                >
                  <option value="">– Select –</option>
                  {renderRelationshipLevel1Options()}
                </select>
              </label>

              <label style={{ marginBottom: 0, minWidth: 0 }}>
                Relationship L2
                <select
                  value={relEntry.relationship_level2}
                  onChange={(e) => updateRel({ relationship_level2: e.target.value })}
                  disabled={!level1}
                  style={relationshipRowControlStyle}
                  title={relEntry.relationship_level2 || "Relationship L2"}
                >
                  <option value="">– Select –</option>
                  {renderRelationshipLevel2Options(level1)}
                </select>
              </label>

              <label style={{ marginBottom: 0, minWidth: 0 }}>
                Sentiment
                <select
                  value={relEntry.sentiment}
                  onChange={(e) => updateRel({ sentiment: e.target.value })}
                  style={relationshipRowControlStyle}
                  title={relEntry.sentiment || "Sentiment"}
                >
                  <option value="">– Select –</option>
                  {SENTIMENT_TAGS.map((tag) => (
                    <option key={tag} value={tag}>
                      {tag}
                    </option>
                  ))}
                </select>
              </label>

              <label style={{ marginBottom: 0, minWidth: 0 }}>
                Target
                <select
                  value={targets.length === 1 ? (targets[0] || "") : relEntry.target}
                  onChange={(e) => updateRel({ target: e.target.value })}
                  disabled={targets.length <= 1}
                  style={relationshipRowControlStyle}
                  title={(targets.length === 1 ? targets[0] : relEntry.target) || "Target"}
                >
                  <option value="">– Select –</option>
                  {targets.map((name) => (
                    <option key={name} value={name}>
                      {name}
                    </option>
                  ))}
                </select>
              </label>

              <div style={{ paddingTop: "1.15rem" }}>
                <button
                  type="button"
                  className="ghost-btn"
                  style={{ padding: "0 0.45rem", height: "32px", marginBottom: 0, alignSelf: "end" }}
                  onClick={() => {
                    const current = ensureAtLeastOneRelationship();
                    setRelationshipMultiList(removeRelationshipMultiRow(current, relIdx));
                  }}
                  title="Remove relationship"
                >
                  ×
                </button>
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  const renderRelationshipSection = ({
    item,
    idx,
    multiRel,
    agents,
    targets,
    effectiveRelationshipLevel1,
    effectiveRelationshipLevel2,
    ensureAtLeastOneRelationship,
    setRelationshipMultiList
  }) => {
    if (item.target_type !== "character") return null;

    return (
      <>
        {!multiRel ? (
          <div className="grid-3">
            <label>
              Relationship L1
              <select
                value={effectiveRelationshipLevel1}
                onChange={(e) => {
                  // Update level1 and reset level2 in a single update
                  // Also sync relationship_multi for single-relationship case
                  const newLevel1 = e.target.value;
                  updateItem(idx, {
                    relationship_level1: newLevel1,
                    relationship_level2: "",
                    // Clear relationship_multi so save logic uses legacy fields
                    relationship_multi: []
                  });
                }}
              >
                <option value="">– Select –</option>
                {renderRelationshipLevel1Options()}
              </select>
            </label>
            <label>
              Relationship L2
              <select
                value={effectiveRelationshipLevel2}
                onChange={(e) => {
                  // Sync relationship_multi when updating level2
                  updateItem(idx, {
                    relationship_level2: e.target.value,
                    // Clear relationship_multi so save logic uses legacy fields
                    relationship_multi: []
                  });
                }}
                disabled={!effectiveRelationshipLevel1}
              >
                <option value="">– Select –</option>
                {renderRelationshipLevel2Options(effectiveRelationshipLevel1)}
              </select>
            </label>
            <label>
              Sentiment
              <select
                value={item.sentiment || ""}
                onChange={(e) => {
                  // Sync relationship_multi when updating sentiment
                  updateItem(idx, {
                    sentiment: e.target.value,
                    // Clear relationship_multi so save logic uses legacy fields
                    relationship_multi: []
                  });
                }}
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
        ) : (
          renderMultiRelationshipEditor({
            agents,
            targets,
            ensureAtLeastOneRelationship,
            setRelationshipMultiList
          })
        )}
      </>
    );
  };

  const renderAutoAnnotateEventControls = ({ item, idx }) => {
    if (typeof onAutoAnnotateEvent !== "function") return null;

    return (
      <div style={{ marginTop: "0.5rem" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
          <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
            <select
              value={eventAnnotationModes[item.id] || "recreate"}
              onChange={(e) => {
                const mode = e.target.value;
                setEventAnnotationModes(prev => ({ ...prev, [item.id]: mode }));
                // Clear additional prompt when switching to recreate mode
                if (mode === "recreate") {
                  setEventAdditionalPrompts(prev => {
                    const next = { ...prev };
                    delete next[item.id];
                    return next;
                  });
                }
              }}
              disabled={!!(autoAnnotateEventLoading && autoAnnotateEventLoading[item.id])}
              style={{
                padding: "0.4rem 0.5rem",
                fontSize: "0.8rem",
                lineHeight: "1.2",
                border: "1px solid #cbd5e1",
                borderRadius: "6px",
                backgroundColor: "white",
                cursor: (autoAnnotateEventLoading && autoAnnotateEventLoading[item.id]) ? "not-allowed" : "pointer",
                marginBottom: 0,
                width: "auto",
                minWidth: "110px",
                height: "32px",
                boxSizing: "border-box"
              }}
              title="Select annotation mode: Supplement (add missing), Modify (update existing), or Recreate (from scratch)"
            >
              <option value="recreate">Recreate</option>
              <option value="supplement">Supplement</option>
              <option value="modify">Modify</option>
            </select>
            <button
              type="button"
              className="ghost-btn"
              onClick={() => {
                const mode = eventAnnotationModes[item.id] || "recreate";
                const additionalPrompt = eventAdditionalPrompts[item.id] || "";
                onAutoAnnotateEvent(item.id, idx, mode, additionalPrompt);
              }}
              disabled={!!(autoAnnotateEventLoading && autoAnnotateEventLoading[item.id])}
              title="Auto-annotate this event using the LLM backend"
              style={{ minWidth: "100px", whiteSpace: "nowrap", height: "32px" }}
            >
              {(autoAnnotateEventLoading && autoAnnotateEventLoading[item.id]) ? "Annotating…" : "Auto-annotate"}
            </button>
          </div>
          {((eventAnnotationModes[item.id] === "supplement") || (eventAnnotationModes[item.id] === "modify")) && (
            <input
              type="text"
              value={eventAdditionalPrompts[item.id] || ""}
              onChange={(e) => {
                setEventAdditionalPrompts(prev => ({ ...prev, [item.id]: e.target.value }));
              }}
              placeholder="Additional instructions (optional)..."
              disabled={!!(autoAnnotateEventLoading && autoAnnotateEventLoading[item.id])}
              style={{
                padding: "0.4rem 0.5rem",
                fontSize: "0.8rem",
                border: "1px solid #cbd5e1",
                borderRadius: "6px",
                backgroundColor: "white",
                marginBottom: 0,
                width: "100%",
                boxSizing: "border-box"
              }}
              title="Enter additional instructions for the annotation model"
            />
          )}
        </div>
      </div>
    );
  };

  const renderActionSection = ({ item, idx }) => {
    if (item.target_type !== "character") return null;

    return (
      <>
        <div className="grid-3" style={{ marginTop: "0.5rem" }}>
          <label>
            Action Category
            <select
              value={item.action_category || ""}
              onChange={(e) => {
                // Update category and reset action_type and action_context in a single update
                updateItem(idx, {
                  action_category: e.target.value,
                  action_type: "",
                  action_context: ""
                });
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
                // Update action_type and reset context in a single update
                updateItem(idx, {
                  action_type: e.target.value,
                  action_context: ""
                });
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

        {item.action_category && item.action_type && (
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
      </>
    );
  };

  const renderEventHeaderSection = ({ item, idx }) => {
    return (
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
    );
  };

  const renderEventDetailsSection = ({ item, idx }) => {
    return (
      <>
        <div style={{ marginTop: "0.25rem" }}>
          <label>
            Narrative Function
            <select
              value={item.narrative_function || ""}
              onChange={(e) => updateItem(idx, "narrative_function", e.target.value)}
            >
              <option value="">– Select –</option>
              {NARRATIVE_FUNCTIONS.map((fn) => (
                <option key={fn.code} value={fn.code}>
                  {fn.name}
                </option>
              ))}
            </select>
          </label>
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
      </>
    );
  };

  const renderNarrativeItemRow = (item, idx) => {
    const {
      multiRel,
      rmList,
      agents,
      targets,
      effectiveRelationshipLevel1,
      effectiveRelationshipLevel2
    } = deriveRelationshipUiState(item);

    const setRelationshipMultiList = (nextList) => {
      updateItem(idx, buildSetRelationshipMultiUpdates(nextList));
    };

    const ensureAtLeastOneRelationship = () =>
      ensureAtLeastOneRelationshipMulti({ item, rmList, agents, targets });

    return (
      <div key={item.id || idx} className="propp-row">
        {renderEventHeaderSection({ item, idx })}

        {renderEventDetailsSection({ item, idx })}

        {renderRelationshipSection({
          item,
          idx,
          multiRel,
          agents,
          targets,
          effectiveRelationshipLevel1,
          effectiveRelationshipLevel2,
          ensureAtLeastOneRelationship,
          setRelationshipMultiList
        })}

        {renderActionSection({ item, idx })}

        {/* Auto-annotation UI for individual event (placed under Context control) */}
        {renderAutoAnnotateEventControls({ item, idx })}

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
    );
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
          <button
            type="button"
            className="ghost-btn"
            onClick={() => {
              setNarrativeStructure([]);
              if (typeof setHighlightedRanges === "function") setHighlightedRanges({});
            }}
            style={{
              fontSize: "0.85rem",
              padding: "0.4rem 0.8rem",
              color: "#ef4444",
              borderColor: "#ef4444"
            }}
            title="Clear all narrative events"
          >
            Clear
          </button>
        </div>
      </div>

      {typeof onAutoSegmentNarratives === "function" && (
        <div style={{ marginTop: "0.5rem", marginBottom: "0.75rem", display: "flex", justifyContent: "flex-end" }}>
          <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
            <select
              value={autoSegmentMode}
              onChange={(e) => setAutoSegmentMode(e.target.value)}
              disabled={!!autoSegmentNarrativesLoading}
              style={{
                padding: "0.4rem 0.5rem",
                fontSize: "0.85rem",
                lineHeight: "1.2",
                border: "1px solid #cbd5e1",
                borderRadius: "6px",
                backgroundColor: "white",
                width: "auto",
                minWidth: "170px",
                height: "32px",
                boxSizing: "border-box",
                marginBottom: 0
              }}
              title="Choose segmentation mode"
            >
              <option value="llm_only">LLM only</option>
              <option value="embedding_assisted">Embedding assisted</option>
            </select>
            <button
              type="button"
              className="ghost-btn"
              onClick={() => onAutoSegmentNarratives(autoSegmentMode)}
              disabled={!!autoSegmentNarrativesLoading}
              style={{
                fontSize: "0.85rem",
                padding: "0.4rem 0.8rem",
                minWidth: "180px",
                whiteSpace: "nowrap",
                height: "32px",
                boxSizing: "border-box",
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                lineHeight: "1.2",
                marginBottom: 0
              }}
              title="Auto-segment the story into narrative spans"
            >
              {autoSegmentNarrativesLoading ? "Sectioning…" : "Automatic sectioning"}
            </button>
          </div>
        </div>
      )}

      {items.map((item, idx) => renderNarrativeItemRow(item, idx))}

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

