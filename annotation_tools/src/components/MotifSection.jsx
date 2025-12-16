import React from "react";
import { ATU_TYPES, MOTIF_CATEGORIES } from "../constants.js";

export default function MotifSection({ motif, setMotif }) {
  const [selectedCategoryCode, setSelectedCategoryCode] = React.useState("");
  const [selectedSubcategory, setSelectedSubcategory] = React.useState("");

  // Ensure motif_type is an array (handle migration from string)
  const motifTypes = Array.isArray(motif.motif_type) 
    ? motif.motif_type 
    : (motif.motif_type ? [motif.motif_type] : []);

  // Get selected category's subcategories
  const selectedCategory = MOTIF_CATEGORIES.find(cat => cat.code === selectedCategoryCode);
  const subcategories = selectedCategory ? selectedCategory.subcategories : [];

  const handleCategoryChange = (e) => {
    const code = e.target.value;
    setSelectedCategoryCode(code);
    setSelectedSubcategory(""); // Reset subcategory when category changes
  };

  const handleSubcategoryChange = (e) => {
    const subcategoryValue = e.target.value;
    setSelectedSubcategory(subcategoryValue);
  };

  const handleAddMotif = () => {
    if (!selectedCategoryCode || !selectedSubcategory) return;
    
    const subcategory = subcategories.find(sub => sub.range === selectedSubcategory);
    if (!subcategory) return;

    // Format: "A: A0 - A99 - Creator"
    const formatted = `${selectedCategoryCode}: ${subcategory.range} - ${subcategory.description}`;
    
    // Ensure motif_type is an array
    const currentTypes = Array.isArray(motif.motif_type) 
      ? motif.motif_type 
      : (motif.motif_type ? [motif.motif_type] : []);
    
    // Check if already exists
    if (currentTypes.includes(formatted)) {
      // Already added, just reset selection
      setSelectedCategoryCode("");
      setSelectedSubcategory("");
      return;
    }

    // Add to array
    const updatedTypes = [...currentTypes, formatted];
    setMotif({ ...motif, motif_type: updatedTypes });
    
    // Reset selection after adding
    setSelectedCategoryCode("");
    setSelectedSubcategory("");
  };

  const handleRemoveMotif = (index) => {
    // Ensure motif_type is an array
    const currentTypes = Array.isArray(motif.motif_type) 
      ? motif.motif_type 
      : (motif.motif_type ? [motif.motif_type] : []);
    const updatedTypes = currentTypes.filter((_, i) => i !== index);
    setMotif({ ...motif, motif_type: updatedTypes });
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
            value={selectedSubcategory}
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

      {selectedCategoryCode && selectedSubcategory && (
        <button
          type="button"
          className="ghost-btn"
          onClick={handleAddMotif}
          style={{ marginTop: "0.5rem" }}
        >
          + Add Selected Motif
        </button>
      )}

      {motifTypes.length > 0 && (
        <div style={{ marginTop: "1rem" }}>
          <div className="section-header-row">
            <span>Selected Motifs ({motifTypes.length})</span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            {motifTypes.map((type, index) => (
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
                <span style={{ flex: 1 }}>{type}</span>
                <button
                  type="button"
                  className="ghost-btn"
                  onClick={() => handleRemoveMotif(index)}
                  style={{ padding: "0.25rem 0.5rem", fontSize: "0.875rem" }}
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
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

