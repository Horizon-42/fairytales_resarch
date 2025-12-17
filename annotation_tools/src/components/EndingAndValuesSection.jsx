import React from "react";
import { ENDING_TYPES, VALUE_TYPES } from "../constants.js";

export default function EndingAndValuesSection({ meta, setMeta }) {
  // Key values selector state
  const [selectedKeyValue, setSelectedKeyValue] = React.useState("");

  // Ensure key_values is an array
  const keyValues = Array.isArray(meta.key_values)
    ? meta.key_values
    : (meta.key_values ? [meta.key_values] : []);

  const handleAddKeyValue = () => {
    if (!selectedKeyValue) return;

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
              onChange={(e) => setSelectedKeyValue(e.target.value)}
            >
              <option value="">– Select Key Value –</option>
              {VALUE_TYPES.filter(v => !keyValues.includes(v)).map((v) => (
                <option key={v} value={v}>
                  {v}
                </option>
              ))}
            </select>
          </label>
          {selectedKeyValue && (
            <button
              type="button"
              className="ghost-btn"
              onClick={handleAddKeyValue}
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
