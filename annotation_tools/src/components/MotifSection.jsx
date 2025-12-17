import React from "react";
import { MOTIF_CATEGORIES, ATU_CATEGORY_ROWS } from "../constants.js";

export default function MotifSection({ motif, setMotif }) {
  const [selectedCategoryCode, setSelectedCategoryCode] = React.useState("");
  const [selectedSubcategory, setSelectedSubcategory] = React.useState("");
  const [selectedATULevel1, setSelectedATULevel1] = React.useState("");
  const [selectedATULevel2, setSelectedATULevel2] = React.useState("");
  const [selectedATULevel3, setSelectedATULevel3] = React.useState("");

  // Ensure motif_type is an array (handle migration from string)
  const motifTypes = Array.isArray(motif.motif_type) 
    ? motif.motif_type 
    : (motif.motif_type ? [motif.motif_type] : []);

  // Ensure ATU category selections are an array
  const atuSelections = Array.isArray(motif.atu_categories)
    ? motif.atu_categories
    : (motif.atu_categories ? [motif.atu_categories] : []);

  // Get selected category's subcategories
  const selectedCategory = MOTIF_CATEGORIES.find(cat => cat.code === selectedCategoryCode);
  const subcategories = selectedCategory ? selectedCategory.subcategories : [];

  // ATU three-level hierarchy derived from ATU_CATEGORY_ROWS
  const level1Rows = React.useMemo(
    () => ATU_CATEGORY_ROWS.filter(r => r.level === 1),
    []
  );

  const selectedLevel1Row = React.useMemo(
    () => level1Rows.find(r => `${r.start}-${r.end}` === selectedATULevel1) || null,
    [level1Rows, selectedATULevel1]
  );

  const level2Rows = React.useMemo(() => {
    if (!selectedLevel1Row) return [];
    return ATU_CATEGORY_ROWS.filter(
      r =>
        r.level === 2 &&
        r.start >= selectedLevel1Row.start &&
        r.end <= selectedLevel1Row.end
    );
  }, [selectedLevel1Row]);

  const selectedLevel2Row = React.useMemo(
    () => level2Rows.find(r => `${r.start}-${r.end}` === selectedATULevel2) || null,
    [level2Rows, selectedATULevel2]
  );

  const level3Rows = React.useMemo(() => {
    if (!selectedLevel2Row) return [];
    return ATU_CATEGORY_ROWS.filter(
      r =>
        r.level === 3 &&
        r.start >= selectedLevel2Row.start &&
        r.end <= selectedLevel2Row.end
    );
  }, [selectedLevel2Row]);

  const handleCategoryChange = (e) => {
    const code = e.target.value;
    setSelectedCategoryCode(code);
    setSelectedSubcategory(""); // Reset subcategory when category changes
  };

  const handleSubcategoryChange = (e) => {
    const subcategoryValue = e.target.value;
    setSelectedSubcategory(subcategoryValue);
  };

  const handleATULevel1Change = (e) => {
    const value = e.target.value;
    setSelectedATULevel1(value);
    // Reset deeper levels
    setSelectedATULevel2("");
    setSelectedATULevel3("");
  };

  const handleATULevel2Change = (e) => {
    const value = e.target.value;
    setSelectedATULevel2(value);
    // Reset level 3
    setSelectedATULevel3("");
  };

  const handleATULevel3Change = (e) => {
    const value = e.target.value;
    setSelectedATULevel3(value);
  };

  const handleAddATUCategory = () => {
    if (!selectedATULevel1) return;

    const l1 = selectedLevel1Row;
    const l2 = selectedLevel2Row;
    const l3 =
      level3Rows.find(r => `${r.start}-${r.end}` === selectedATULevel3) || null;

    // Choose the most specific available level
    const chosen = l3 || l2 || l1;
    if (!chosen) return;

    const parts = [];
    if (l1) parts.push(l1.name);
    if (l2) parts.push(l2.name);
    if (l3) parts.push(l3.name);
    const pathLabel = parts.join(" > ");

    const label = `ATU ${chosen.start}-${chosen.end}: ${pathLabel}`;

    if (atuSelections.includes(label)) {
      // Already selected, just reset selection
      setSelectedATULevel1("");
      setSelectedATULevel2("");
      setSelectedATULevel3("");
      return;
    }

    const next = [...atuSelections, label];
    setMotif({ ...motif, atu_categories: next });

    setSelectedATULevel1("");
    setSelectedATULevel2("");
    setSelectedATULevel3("");
  };

  const handleRemoveATUCategory = (index) => {
    const next = atuSelections.filter((_, i) => i !== index);
    setMotif({ ...motif, atu_categories: next });
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
      {/* ATU three-level category selector (multi-select) */}
      <div style={{ marginTop: "0.75rem" }}>
        <div className="section-header-row">
          <span>ATU Categories (multi-select)</span>
        </div>
        <div className="grid-2" style={{ marginTop: "0.25rem" }}>
          <label>
            ATU Level 1
            <select value={selectedATULevel1} onChange={handleATULevel1Change}>
              <option value="">– Select Level 1 –</option>
              {level1Rows.map((row) => (
                <option
                  key={`${row.start}-${row.end}`}
                  value={`${row.start}-${row.end}`}
                >
                  {row.start}-{row.end} – {row.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            ATU Level 2
            <select
              value={selectedATULevel2}
              onChange={handleATULevel2Change}
              disabled={!selectedATULevel1 || level2Rows.length === 0}
            >
              <option value="">– Select Level 2 –</option>
              {level2Rows.map((row) => (
                <option
                  key={`${row.start}-${row.end}`}
                  value={`${row.start}-${row.end}`}
                >
                  {row.start}-{row.end} – {row.name}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div style={{ marginTop: "0.25rem" }}>
          <label>
            ATU Level 3
            <select
              value={selectedATULevel3}
              onChange={handleATULevel3Change}
              disabled={!selectedATULevel2 || level3Rows.length === 0}
            >
              <option value="">– Select Level 3 –</option>
              {level3Rows.map((row) => (
                <option
                  key={`${row.start}-${row.end}`}
                  value={`${row.start}-${row.end}`}
                >
                  {row.start}-{row.end} – {row.name}
                </option>
              ))}
            </select>
          </label>
        </div>
        {(selectedATULevel1 || selectedATULevel2 || selectedATULevel3) && (
          <button
            type="button"
            className="ghost-btn"
            onClick={handleAddATUCategory}
            style={{ marginTop: "0.5rem" }}
          >
            + Add Selected ATU
          </button>
        )}
      </div>

      {atuSelections.length > 0 && (
        <div style={{ marginTop: "0.75rem" }}>
          <div className="section-header-row">
            <span>Selected ATU Categories ({atuSelections.length})</span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            {atuSelections.map((item, index) => (
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
                <span style={{ flex: 1 }}>{item}</span>
                <button
                  type="button"
                  className="ghost-btn"
                  onClick={() => handleRemoveATUCategory(index)}
                  style={{ padding: "0.25rem 0.5rem", fontSize: "0.875rem" }}
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

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

