import React from "react";
import { ENDING_TYPES, VALUE_TYPES } from "../constants.js";

export default function EndingAndValuesSection({ meta, setMeta }) {
  // Key values selector state
  const [selectedKeyValue, setSelectedKeyValue] = React.useState("");
  const [otherValueText, setOtherValueText] = React.useState("");

  // Ensure key_values is an array
  const keyValues = Array.isArray(meta.key_values)
    ? meta.key_values
    : (meta.key_values ? [meta.key_values] : []);

  // Check if "OTHER" (with or without custom text) is already selected
  const hasOther = keyValues.some(v => v.startsWith("OTHER"));

  const handleAddKeyValue = () => {
    if (!selectedKeyValue) return;

    // If OTHER is selected, require custom text
    if (selectedKeyValue === "OTHER") {
      if (!otherValueText.trim()) {
        return; // Don't add if no custom text provided
      }
      const otherValue = `OTHER (${otherValueText.trim()})`;
      if (keyValues.includes(otherValue)) {
        setSelectedKeyValue("");
        setOtherValueText("");
        return;
      }
      const updated = [...keyValues, otherValue];
      setMeta({ ...meta, key_values: updated });
      setSelectedKeyValue("");
      setOtherValueText("");
      return;
    }

    // For non-OTHER values
    if (keyValues.includes(selectedKeyValue)) {
      setSelectedKeyValue("");
      return;
    }

    const updated = [...keyValues, selectedKeyValue];
    setMeta({ ...meta, key_values: updated });
    setSelectedKeyValue("");
  };

  const handleRemoveKeyValue = (index) => {
    const updated = keyValues.filter((_, i) => i !== index);
    setMeta({ ...meta, key_values: updated });
  };

  // Filter out OTHER from dropdown if it's already selected
  const availableValues = VALUE_TYPES.filter(v => {
    if (v === "OTHER" && hasOther) {
      return false;
    }
    return !keyValues.includes(v);
  });

  return (
    <section className="card">
      <h2>Ending Type & Key Values</h2>

      <div style={{ marginTop: "0.75rem" }}>
        <label>
          Ending type
          <select
            value={meta.ending_type}
            onChange={(e) =>
              setMeta({ ...meta, ending_type: e.target.value })
            }
          >
            {ENDING_TYPES.map((et) => (
              <option key={et} value={et}>
                {et}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div style={{ marginTop: "0.75rem" }}>
        <div className="section-header-row">
          <span>Key Values (multi-select)</span>
        </div>
        <div style={{ marginTop: "0.25rem" }}>
          <label>
            <select
              value={selectedKeyValue}
              onChange={(e) => {
                setSelectedKeyValue(e.target.value);
                if (e.target.value !== "OTHER") {
                  setOtherValueText("");
                }
              }}
            >
              <option value="">– Select Key Value –</option>
              {availableValues.map((v) => (
                <option key={v} value={v}>
                  {v}
                </option>
              ))}
            </select>
          </label>

          {selectedKeyValue === "OTHER" && (
            <div style={{ marginTop: "0.5rem" }}>
              <label>
                Custom value (required)
                <input
                  type="text"
                  value={otherValueText}
                  onChange={(e) => setOtherValueText(e.target.value)}
                  placeholder="Enter custom key value"
                  style={{ width: "100%", marginTop: "0.25rem" }}
                />
              </label>
            </div>
          )}

          {selectedKeyValue && (
            <button
              type="button"
              className="ghost-btn"
              onClick={handleAddKeyValue}
              disabled={selectedKeyValue === "OTHER" && !otherValueText.trim()}
              style={{ marginTop: "0.5rem" }}
            >
              + Add Selected Key Value
            </button>
          )}
        </div>
      </div>

      {keyValues.length > 0 && (
        <div style={{ marginTop: "0.75rem" }}>
          <div className="section-header-row">
            <span>Selected Key Values ({keyValues.length})</span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            {keyValues.map((value, index) => (
              <div
                key={index}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "0.5rem",
                  background: "#f3f4f6",
                  borderRadius: "4px",
                  gap: "0.5rem"
                }}
              >
                <span style={{ flex: 1 }}>{value}</span>
                <button
                  type="button"
                  className="ghost-btn"
                  onClick={() => handleRemoveKeyValue(index)}
                  style={{ padding: "0.25rem 0.5rem", fontSize: "0.875rem" }}
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
