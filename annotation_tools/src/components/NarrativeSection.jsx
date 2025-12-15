import React from "react";
import CreatableSelect from 'react-select/creatable';
import { PROPP_FUNCTIONS, TARGET_CATEGORIES, OBJECT_TYPES } from "../constants.js";
import { generateUUID } from "../utils/fileHandler.js";
import { customSelectStyles } from "../utils/helpers.js";

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

  const items = narrativeStructure.map((item) => {
    if (typeof item === "string") {
      return {
        id: generateUUID(),
        event_type: "OTHER",
        description: item,
        agents: [],
        targets: [],
        text_span: null,
        target_type: "",
        object_type: "",
        instrument: ""
      };
    }
    if (!item.id) {
      return { ...item, id: generateUUID() };
    }
    return item;
  });

  const updateItem = (index, field, value) => {
    const next = [...items];
    next[index] = { ...next[index], [field]: value };
    setNarrativeStructure(next);

    if (onAddProppFn && field === "event_type") {
      const updatedItem = { ...next[index], [field]: value };
      onAddProppFn(updatedItem);
    }
  };

  const addItem = () => {
    setNarrativeStructure([
      ...items,
      {
        id: generateUUID(),
        event_type: "",
        description: "",
        agents: [],
        targets: [],
        text_span: null,
        target_type: "",
        object_type: "",
        instrument: ""
      }
    ]);
  };

  const removeItem = (index) => {
    const next = items.filter((_, i) => i !== index);
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
      if (next[key]) {
        delete next[key];
      } else {
        next[key] = {
          start: span.start,
          end: span.end,
          color: "#fca5a5"
        };
      }
      return next;
    });
  };

  const isHighlighted = (idx) => {
    return highlightedRanges && !!highlightedRanges[`narrative-${idx}`];
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

  const handleAmbiguousMotifsChange = (idx, value) => {
    const current = crossValidation.bias_reflection.ambiguous_motifs || [];
    const next = [...current];
    next[idx] = value;
    setCrossValidation({
      ...crossValidation,
      bias_reflection: {
        ...crossValidation.bias_reflection,
        ambiguous_motifs: next
      }
    });
  };

  const addAmbiguousMotif = () => {
    const current = crossValidation.bias_reflection.ambiguous_motifs || [];
    setCrossValidation({
      ...crossValidation,
      bias_reflection: {
        ...crossValidation.bias_reflection,
        ambiguous_motifs: [...current, ""]
      }
    });
  };

  return (
    <section className="card">
      <h2>Narrative Events</h2>
      <div className="section-header-row">
        <span>Story Sequence</span>
      </div>

      {items.map((item, idx) => (
        <div key={idx} className="propp-row">
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
                    {fn}
                  </option>
                ))}
                <option value="OTHER">OTHER</option>
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
                    background: isHighlighted(idx) ? "#fca5a5" : undefined,
                    color: isHighlighted(idx) ? "#000" : undefined,
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
          
          <button
            type="button"
            className="ghost-btn"
            style={{ color: "#ef4444", borderColor: "#ef4444", marginTop: "0.5rem" }}
            onClick={() => removeItem(idx)}
          >
            Remove Event
          </button>
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
      <label>
        Hero/villain mapping
        <textarea
          rows={2}
          value={crossValidation.bias_reflection.hero_villain_mapping}
          onChange={(e) =>
            handleBiasChange("hero_villain_mapping", e.target.value)
          }
        />
      </label>

      <div className="section-header-row">
        <span>Ambiguous motifs</span>
        <button
          type="button"
          className="ghost-btn"
          onClick={addAmbiguousMotif}
        >
          + Add motif
        </button>
      </div>
      {(crossValidation.bias_reflection.ambiguous_motifs || []).map(
        (m, idx) => (
          <input
            key={idx}
            value={m}
            onChange={(e) => handleAmbiguousMotifsChange(idx, e.target.value)}
          />
        )
      )}
    </section>
  );
}

