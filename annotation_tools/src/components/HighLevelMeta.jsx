import React from "react";
import { ATU_TYPES, VALUE_TYPES, ENDING_TYPES } from "../constants.js";
import { multiSelectFromEvent } from "../utils/helpers.js";

export default function HighLevelMeta({ meta, setMeta, deepMeta, setDeepMeta }) {
  const handleValuesChange = (e) => {
    const values = multiSelectFromEvent(e);
    setDeepMeta({ ...deepMeta, key_values: values });
  };

  return (
    <section className="card">
      <h2>High-level labels (ATU, values, ending)</h2>
      <div className="grid-2">
        <label>
          ATU type
          <select
            value={meta.atu_type}
            onChange={(e) => setMeta({ ...meta, atu_type: e.target.value })}
          >
            <option value="">–</option>
            {ATU_TYPES.map((code) => (
              <option key={code} value={code}>
                {code}
              </option>
            ))}
          </select>
        </label>
        <label>
          Main motif (free text)
          <input
            value={meta.main_motif}
            onChange={(e) =>
              setMeta({ ...meta, main_motif: e.target.value })
            }
            placeholder="ATU_313"
          />
        </label>
      </div>

      <label className="checkbox-inline">
        <input
          type="checkbox"
          checked={meta.target_motif}
          onChange={(e) =>
            setMeta({ ...meta, target_motif: e.target.checked })
          }
        />
        Target motif story?
      </label>

      <hr />

      <h3>Deep meta</h3>
      <div className="grid-2">
        <label>
          Ending type (deep)
          <select
            value={deepMeta.ending_type}
            onChange={(e) =>
              setDeepMeta({ ...deepMeta, ending_type: e.target.value })
            }
          >
            {ENDING_TYPES.map((et) => (
              <option key={et} value={et}>
                {et}
              </option>
            ))}
          </select>
        </label>
        <label>
          Key values (deep)
          <select
            multiple
            value={deepMeta.key_values}
            onChange={handleValuesChange}
          >
            {VALUE_TYPES.map((v) => (
              <option key={v} value={v}>
                {v}
              </option>
            ))}
          </select>
        </label>
      </div>
    </section>
  );
}

