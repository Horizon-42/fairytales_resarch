import React from "react";
import CreatableSelect from 'react-select/creatable';
import { ENDING_TYPES, VALUE_TYPES } from "../constants.js";
import { customSelectStyles } from "../utils/helpers.js";

export default function EndingAndValuesSection({ meta, setMeta }) {
  // Ensure key_values is an array
  const keyValues = Array.isArray(meta.key_values)
    ? meta.key_values
    : (meta.key_values ? [meta.key_values] : []);

  // Create options for key values selector
  const keyValueOptions = VALUE_TYPES.map(v => ({
    label: v,
    value: v
  }));

  // Get current key values as selector format
  const getKeyValuesForSelector = () => {
    return keyValues.map(value => {
      // Check if it's already in the format we need
      const found = keyValueOptions.find(opt => opt.value === value);
      if (found) {
        return found;
      }
      // For custom values (like "OTHER (custom text)"), create a new option
      return {
        label: value,
        value: value
      };
    });
  };

  // Handle key values change from selector
  const handleKeyValuesChange = (selectedOptions) => {
    const values = selectedOptions ? selectedOptions.map(opt => opt.value) : [];
    setMeta({ ...meta, key_values: values });
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
        <label>
          Key Values (multi-select)
          <CreatableSelect
            isMulti
            options={keyValueOptions}
            value={getKeyValuesForSelector()}
            onChange={handleKeyValuesChange}
            placeholder="Select or create key values..."
            styles={customSelectStyles}
            formatCreateLabel={(inputValue) => `Create "OTHER (${inputValue})"`}
          />
        </label>
        <p className="hint" style={{ marginTop: "0.25rem", fontSize: "0.875rem", color: "#64748b" }}>
          You can select multiple values. Type to create custom values like "OTHER (your text)".
        </p>
      </div>
    </section>
  );
}
