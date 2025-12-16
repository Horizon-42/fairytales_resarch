import React from "react";
import { ATU_TYPES, MOTIF_CATEGORIES } from "../constants.js";

export default function MotifSection({ motif, setMotif }) {
  const [selectedCategoryCode, setSelectedCategoryCode] = React.useState("");

  // Get selected category's subcategories
  const selectedCategory = MOTIF_CATEGORIES.find(cat => cat.code === selectedCategoryCode);
  const subcategories = selectedCategory ? selectedCategory.subcategories : [];

  // Parse current motif_type value to extract category and subcategory
  React.useEffect(() => {
    if (motif.motif_type) {
      // Try to extract category code from motif_type
      // Format examples: "A: A0 - A99 - Creator" or "A0 - A99" or "A: A0 - A99"
      const match = motif.motif_type.match(/^([A-Z]):?\s*([A-Z]\d+\s*-\s*[A-Z]\d+)/);
      if (match) {
        setSelectedCategoryCode(match[1]);
      } else {
        // Try to match just the range (e.g., "A0 - A99")
        const rangeMatch = motif.motif_type.match(/^([A-Z])\d+/);
        if (rangeMatch) {
          setSelectedCategoryCode(rangeMatch[1]);
        }
      }
    } else {
      // Clear selection when motif_type is empty
      setSelectedCategoryCode("");
    }
  }, [motif.motif_type]);

  const handleCategoryChange = (e) => {
    const code = e.target.value;
    setSelectedCategoryCode(code);
    // Clear motif_type when category changes
    setMotif({ ...motif, motif_type: "" });
  };

  const handleSubcategoryChange = (e) => {
    const subcategoryValue = e.target.value;
    if (subcategoryValue) {
      // Format: "A: A0 - A99 - Creator"
      const subcategory = subcategories.find(sub => sub.range === subcategoryValue);
      if (subcategory) {
        const formatted = `${selectedCategoryCode}: ${subcategory.range} - ${subcategory.description}`;
        setMotif({ ...motif, motif_type: formatted });
      }
    } else {
      setMotif({ ...motif, motif_type: "" });
    }
  };

  // Get current subcategory value from motif_type
  const getCurrentSubcategory = () => {
    if (!motif.motif_type || !selectedCategory) return "";
    // Extract range from motif_type (format: "A: A0 - A99 - Creator" or "A0 - A99")
    const match = motif.motif_type.match(/([A-Z]\d+\s*-\s*[A-Z]\d+)/);
    if (match) {
      const range = match[1].trim();
      // Verify this range exists in the selected category
      const exists = selectedCategory.subcategories.some(sub => sub.range === range);
      return exists ? range : "";
    }
    return "";
  };
  const handleObstaclePatternChange = (index, value) => {
    const next = [...motif.obstacle_pattern];
    next[index] = value;
    setMotif({ ...motif, obstacle_pattern: next });
  };

  const addObstacleRow = () => {
    setMotif({
      ...motif,
      obstacle_pattern: [...motif.obstacle_pattern, ""]
    });
  };

  return (
    <section className="card">
      <h2>Motifs</h2>
      <label>
        Motif ATU type
        <select
          value={motif.atu_type}
          onChange={(e) => setMotif({ ...motif, atu_type: e.target.value })}
        >
          <option value="">–</option>
          {ATU_TYPES.map((code) => (
            <option key={code} value={code}>
              {code}
            </option>
          ))}
        </select>
      </label>

      <div className="grid-2">
        <label>
          Motif Category
          <select
            value={selectedCategoryCode}
            onChange={handleCategoryChange}
          >
            <option value="">– Select Category –</option>
            {MOTIF_CATEGORIES.map((cat) => (
              <option key={cat.code} value={cat.code}>
                {cat.code} - {cat.category}
              </option>
            ))}
          </select>
        </label>
        <label>
          Motif Sub-category
          <select
            value={getCurrentSubcategory()}
            onChange={handleSubcategoryChange}
            disabled={!selectedCategoryCode}
          >
            <option value="">– Select Sub-category –</option>
            {subcategories.map((sub) => (
              <option key={sub.range} value={sub.range}>
                {sub.range} - {sub.description}
              </option>
            ))}
          </select>
        </label>
      </div>
      
      {motif.motif_type && (
        <div style={{ marginTop: "0.5rem", padding: "0.5rem", background: "#f3f4f6", borderRadius: "4px" }}>
          <strong>Selected:</strong> {motif.motif_type}
        </div>
      )}

      <div>
        <div className="section-header-row">
          <span>Obstacle pattern</span>
          <button
            type="button"
            className="ghost-btn"
            onClick={addObstacleRow}
          >
            + Add obstacle
          </button>
        </div>
        {motif.obstacle_pattern.length === 0 && (
          <p className="hint">
            Use the button above to add motifs like COMB_TO_FOREST, etc.
          </p>
        )}
        {motif.obstacle_pattern.map((val, idx) => (
          <input
            key={idx}
            value={val}
            onChange={(e) => handleObstaclePatternChange(idx, e.target.value)}
            placeholder="COMB_TO_FOREST"
          />
        ))}
      </div>

      <label>
        Thinking process (short note)
        <textarea
          rows={3}
          value={motif.thinking_process}
          onChange={(e) =>
            setMotif({ ...motif, thinking_process: e.target.value })
          }
        />
      </label>
    </section>
  );
}

