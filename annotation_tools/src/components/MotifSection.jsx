import React from "react";
import { MOTIF_CATEGORIES } from "../constants.js";
import { ATU_HIERARCHY } from "../atu_hierarchy.js";

export default function MotifSection({ motif, setMotif }) {
  const [selectedCategoryCode, setSelectedCategoryCode] = React.useState("");
  const [selectedSubcategory, setSelectedSubcategory] = React.useState("");
  const [selectedATULevel1, setSelectedATULevel1] = React.useState("");
  const [selectedATULevel2, setSelectedATULevel2] = React.useState("");
  const [selectedATULevel3, setSelectedATULevel3] = React.useState("");
  const [selectedATULevel4, setSelectedATULevel4] = React.useState("");

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

  // ATU hierarchy from CSV-based structure
  const level1Items = React.useMemo(() => ATU_HIERARCHY, []);

  const selectedLevel1Item = React.useMemo(
    () => level1Items.find(item => item.key === selectedATULevel1) || null,
    [level1Items, selectedATULevel1]
  );

  const level2Items = React.useMemo(() => {
    if (!selectedLevel1Item) return [];
    return selectedLevel1Item.children || [];
  }, [selectedLevel1Item]);

  const selectedLevel2Item = React.useMemo(
    () => level2Items.find(item => item.key === selectedATULevel2) || null,
    [level2Items, selectedATULevel2]
  );

  const level3Items = React.useMemo(() => {
    if (!selectedLevel2Item) return [];
    return selectedLevel2Item.children || [];
  }, [selectedLevel2Item]);

  const selectedLevel3Item = React.useMemo(
    () => level3Items.find(item => item.key === selectedATULevel3) || null,
    [level3Items, selectedATULevel3]
  );

  const level4Items = React.useMemo(() => {
    if (!selectedLevel3Item) return [];
    return selectedLevel3Item.children || [];
  }, [selectedLevel3Item]);

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
    setSelectedATULevel4("");
  };

  const handleATULevel2Change = (e) => {
    const value = e.target.value;
    setSelectedATULevel2(value);
    // Reset deeper levels
    setSelectedATULevel3("");
    setSelectedATULevel4("");
  };

  const handleATULevel3Change = (e) => {
    const value = e.target.value;
    setSelectedATULevel3(value);
    // Reset level 4
    setSelectedATULevel4("");
  };

  // Auto-select if only one option available at Level 2
  React.useEffect(() => {
    if (selectedATULevel1 && level2Items.length === 1 && !selectedATULevel2 && level2Items[0]) {
      setSelectedATULevel2(level2Items[0].key);
    }
  }, [selectedATULevel1, level2Items, selectedATULevel2]);

  // Auto-select if only one option available at Level 3
  React.useEffect(() => {
    if (selectedATULevel2 && level3Items.length === 1 && !selectedATULevel3 && level3Items[0]) {
      setSelectedATULevel3(level3Items[0].key);
    }
  }, [selectedATULevel2, level3Items, selectedATULevel3]);

  // Auto-select if only one option available at Level 4
  React.useEffect(() => {
    if (selectedATULevel3 && level4Items.length === 1 && !selectedATULevel4 && level4Items[0]) {
      setSelectedATULevel4(level4Items[0].key);
    }
  }, [selectedATULevel3, level4Items, selectedATULevel4]);

  const handleATULevel4Change = (e) => {
    const value = e.target.value;
    setSelectedATULevel4(value);
  };

  const handleAddATUCategory = () => {
    // Helper function to build path label, skipping "general" at level 3
    const buildPathLabel = () => {
      const parts = [];
      if (selectedLevel1Item) parts.push(selectedLevel1Item.name);
      if (selectedLevel2Item) parts.push(selectedLevel2Item.name);
      // Skip level 3 if it's "general"
      if (selectedLevel3Item && selectedLevel3Item.name !== "general") {
        parts.push(selectedLevel3Item.name);
      }
      return parts.join(" > ");
    };

    // Helper function to get all level 4 items from the selected level
    const getAllLevel4Items = () => {
      if (selectedLevel3Item && selectedLevel3Item.children) {
        return selectedLevel3Item.children.filter(item => item.level === 4);
      }
      if (selectedLevel2Item && selectedLevel2Item.children) {
        // Get all level 4 items from all level 3 children
        const allLevel4Items = [];
        selectedLevel2Item.children.forEach(level3 => {
          if (level3.children) {
            level3.children.forEach(item => {
              if (item.level === 4) {
                allLevel4Items.push(item);
              }
            });
          }
        });
        return allLevel4Items;
      }
      return [];
    };

    // Helper function to calculate ATU range from level4Items
    const calculateATURange = () => {
      const allLevel4Items = getAllLevel4Items();
      if (allLevel4Items.length === 0) return null;
      const numbers = allLevel4Items.map(item => parseInt(item.number)).filter(n => !isNaN(n));
      if (numbers.length === 0) return null;
      const min = Math.min(...numbers);
      const max = Math.max(...numbers);
      return min === max ? `${min}` : `${min}-${max}`;
    };

    // If level 4 (specific ATU) is selected, use that
    if (selectedATULevel4) {
      const atuItem = level4Items.find(item => item.key === selectedATULevel4);
      if (!atuItem) return;

      const pathLabel = buildPathLabel();
      const label = `ATU ${atuItem.number}: ${atuItem.title} (${pathLabel})`;

      if (atuSelections.includes(label)) {
        // Already selected, reset selection
        setSelectedATULevel1("");
        setSelectedATULevel2("");
        setSelectedATULevel3("");
        setSelectedATULevel4("");
        return;
      }

      const next = [...atuSelections, label];
      setMotif({ ...motif, atu_categories: next });

      setSelectedATULevel1("");
      setSelectedATULevel2("");
      setSelectedATULevel3("");
      setSelectedATULevel4("");
      return;
    }

    // Otherwise, add the most specific selected category level
    const chosen = selectedLevel3Item || selectedLevel2Item || selectedLevel1Item;
    if (!chosen) return;

    const pathLabel = buildPathLabel();

    // If level 4 is not selected, add ATU range
    let label;
    const range = calculateATURange();
    if (range) {
      label = `ATU ${range}: ${pathLabel}`;
    } else {
      label = `ATU Category: ${pathLabel}`;
    }

    if (atuSelections.includes(label)) {
      // Already selected, reset selection
      setSelectedATULevel1("");
      setSelectedATULevel2("");
      setSelectedATULevel3("");
      setSelectedATULevel4("");
      return;
    }

    const next = [...atuSelections, label];
    setMotif({ ...motif, atu_categories: next });

    setSelectedATULevel1("");
    setSelectedATULevel2("");
    setSelectedATULevel3("");
    setSelectedATULevel4("");
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
      {/* ATU hierarchical category selector (multi-select) - based on CSV */}
      <div style={{ marginTop: "0.75rem" }}>
        <div className="section-header-row">
          <span>ATU Categories (multi-select)</span>
        </div>
        <div className="grid-2" style={{ marginTop: "0.25rem" }}>
          <label>
            Level 1 (Main Category)
            <select value={selectedATULevel1} onChange={handleATULevel1Change}>
              <option value="">– Select Level 1 –</option>
              {level1Items.map((item) => (
                <option key={item.key} value={item.key}>
                  {item.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Level 2 (Subcategory)
            <select
              value={selectedATULevel2}
              onChange={handleATULevel2Change}
              disabled={!selectedATULevel1 || level2Items.length === 0}
            >
              <option value="">– Select Level 2 –</option>
              {level2Items.map((item) => (
                <option key={item.key} value={item.key}>
                  {item.name}
                </option>
              ))}
            </select>
          </label>
        </div>
        {selectedATULevel2 && level3Items.length > 0 && (
          <div style={{ marginTop: "0.25rem" }}>
            <label>
              Level 3 (Sub-subcategory)
              <select
                value={selectedATULevel3}
                onChange={handleATULevel3Change}
                disabled={!selectedATULevel2}
              >
                <option value="">– Select Level 3 (optional) –</option>
                {level3Items.map((item) => (
                  <option key={item.key} value={item.key}>
                    {item.name}
                  </option>
                ))}
              </select>
            </label>
          </div>
        )}
        {selectedATULevel3 && level4Items.length > 0 && (
          <div style={{ marginTop: "0.25rem" }}>
            <label>
              Level 4 (Specific ATU)
              <select
                value={selectedATULevel4}
                onChange={handleATULevel4Change}
                disabled={!selectedATULevel3}
              >
                <option value="">– Select Specific ATU (optional) –</option>
                {level4Items.map((item) => (
                  <option key={item.key} value={item.key}>
                    ATU {item.number}: {item.title}
                  </option>
                ))}
              </select>
            </label>
          </div>
        )}
        {(selectedATULevel1 || selectedATULevel2 || selectedATULevel3 || selectedATULevel4) && (
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

