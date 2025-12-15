import React, { useMemo } from "react";
import { PROPP_FUNCTIONS } from "../constants.js";
import { emptyProppFn } from "../utils/helpers.js";

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

export default function ProppSection({
  proppFns,
  setProppFns,
  proppNotes,
  setProppNotes,
  currentSelection,
  onSync,
  highlightedRanges,
  setHighlightedRanges,
  narrativeStructure
}) {
  const validNarrativeIds = useMemo(() => {
    return new Set((narrativeStructure || []).map(n => n.id).filter(Boolean));
  }, [narrativeStructure]);

  const handleProppChange = (idx, field, value) => {
    const next = proppFns.map((item, i) =>
      i === idx
        ? {
            ...item,
            [field]:
              field === "textSpan"
                ? { ...item[field], ...value }
                : value
          }
        : item
    );
    setProppFns(next);
  };

  const captureSelection = (idx) => {
    if (!currentSelection) return;
    const next = proppFns.map((item, i) =>
      i === idx
        ? {
            ...item,
            textSpan: currentSelection,
            evidence: currentSelection.text
          }
        : item
    );
    setProppFns(next);
  };

  const addPropp = () => {
    setProppFns([...proppFns, emptyProppFn()]);
  };

  const removePropp = (index) => {
    const next = proppFns.filter((_, i) => i !== index);
    setProppFns(next);
  };

  const toggleHighlight = (idx, span) => {
    if (!setHighlightedRanges || !span) return;
    const key = `propp-${idx}`;

    setHighlightedRanges(prev => {
      const next = { ...prev };
      if (next[key]) {
        delete next[key];
      } else {
        next[key] = {
          start: span.start,
          end: span.end,
          color: "#c084fc"
        };
      }
      return next;
    });
  };

  const isHighlighted = (idx) => {
    return highlightedRanges && !!highlightedRanges[`propp-${idx}`];
  };

  return (
    <section className="card">
      <h2>Propp Functions</h2>

      <div className="section-header-row">
        <span>Propp functions</span>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <button type="button" className="ghost-btn" onClick={onSync} title="Create missing Propp functions from Narrative events">
            Sync from Narrative
          </button>
        </div>
      </div>

      {proppFns.map((fnObj, idx) => {
        const isLinked = fnObj.narrative_event_id && validNarrativeIds.has(fnObj.narrative_event_id);
        const isOrphan = fnObj.narrative_event_id && !validNarrativeIds.has(fnObj.narrative_event_id);

        return (
          <div key={idx} className="propp-row" style={isOrphan ? { borderLeft: "4px solid #ef4444", paddingLeft: "8px" } : {}}>
            {isOrphan && (
              <div style={{ color: "#ef4444", fontSize: "0.8rem", marginBottom: "0.5rem", fontWeight: "bold" }}>
                ⚠️ Unlinked from Narrative
              </div>
            )}
            <div className="grid-2">
              <div>
                <label>Function</label>
                <select
                  value={fnObj.fn}
                  onChange={(e) => handleProppChange(idx, "fn", e.target.value)}
                  style={{ width: "100%", minWidth: "300px" }}
                >
                  <option value="">–</option>
                  {PROPP_FUNCTIONS.map((fn) => (
                    <option key={fn} value={fn}>
                      {formatProppFunctionName(fn)}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label>Text Selection</label>
                <div style={{ display: "flex", gap: "0.5rem" }}>
                  <input
                    type="number"
                    value={fnObj.textSpan?.start || 0}
                    readOnly
                    style={{ background: "#e5e7eb", width: "60px" }}
                  />
                  <span style={{ alignSelf: "center" }}>-</span>
                  <input
                    type="number"
                    value={fnObj.textSpan?.end || 0}
                    readOnly
                    style={{ background: "#e5e7eb", width: "60px" }}
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
                      background: isHighlighted(idx) ? "#c084fc" : undefined,
                      color: isHighlighted(idx) ? "#fff" : undefined,
                      fontWeight: isHighlighted(idx) ? "bold" : undefined,
                      whiteSpace: "nowrap"
                    }}
                    onClick={() => toggleHighlight(idx, fnObj.textSpan)}
                    disabled={!fnObj.textSpan}
                  >
                    {isHighlighted(idx) ? "Hide" : "Highlight"}
                  </button>
                </div>
              </div>
            </div>

            <label>
              Evidence
              <textarea
                rows={2}
                value={fnObj.evidence}
                onChange={(e) =>
                  handleProppChange(idx, "evidence", e.target.value)
                }
              />
            </label>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
              {!isLinked && (
                <button
                  type="button"
                  className="ghost-btn"
                  style={{ color: "#ef4444", borderColor: "#ef4444" }}
                  onClick={() => removePropp(idx)}
                >
                  {isOrphan ? "Delete Unlinked Propp" : "Remove Function"}
                </button>
              )}
            </div>
          </div>
        );
      })}

      <button type="button" className="ghost-btn" onClick={addPropp} style={{ marginTop: "1rem" }}>
        + Add function
      </button>

      <label>
        Propp notes
        <textarea
          rows={2}
          value={proppNotes}
          onChange={(e) => setProppNotes(e.target.value)}
        />
      </label>
    </section>
  );
}

