import React from "react";
import { ATU_HIERARCHY } from "../atu_hierarchy.js";
import { MOTIF_HIERARCHY_LEVEL1_3 } from "../motif_hierarchy_level1_3.js";

export default function MotifSection({ motif, setMotif }) {
  const [selectedATULevel1, setSelectedATULevel1] = React.useState("");
  const [selectedATULevel2, setSelectedATULevel2] = React.useState("");
  const [selectedATULevel3, setSelectedATULevel3] = React.useState("");
  const [selectedATULevel4, setSelectedATULevel4] = React.useState("");

  // Motif hierarchy states (4 levels based on Motifs_level1_3.csv)
  const [selectedMotifLevel1, setSelectedMotifLevel1] = React.useState("");
  const [selectedMotifLevel2, setSelectedMotifLevel2] = React.useState("");
  const [selectedMotifLevel3, setSelectedMotifLevel3] = React.useState("");
  const [selectedMotifLevel4, setSelectedMotifLevel4] = React.useState("");

  // Ensure motif_type is an array (handle migration from string)
  const motifTypes = Array.isArray(motif.motif_type) 
    ? motif.motif_type 
    : (motif.motif_type ? [motif.motif_type] : []);

  // Ensure ATU category selections are an array
  const atuSelections = Array.isArray(motif.atu_categories)
    ? motif.atu_categories
    : (motif.atu_categories ? [motif.atu_categories] : []);

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

  // Motif hierarchy from Motifs_level1_3.csv (4 levels)
  const motifLevel1Items = React.useMemo(() => MOTIF_HIERARCHY_LEVEL1_3, []);

  const selectedMotifLevel1Item = React.useMemo(
    () => motifLevel1Items.find(item => item.key === selectedMotifLevel1) || null,
    [motifLevel1Items, selectedMotifLevel1]
  );

  const motifLevel2Items = React.useMemo(() => {
    if (!selectedMotifLevel1Item) return [];
    return selectedMotifLevel1Item.children || [];
  }, [selectedMotifLevel1Item]);

  const selectedMotifLevel2Item = React.useMemo(
    () => motifLevel2Items.find(item => item.key === selectedMotifLevel2) || null,
    [motifLevel2Items, selectedMotifLevel2]
  );

  const motifLevel3Items = React.useMemo(() => {
    if (!selectedMotifLevel2Item) return [];
    return selectedMotifLevel2Item.children || [];
  }, [selectedMotifLevel2Item]);

  const selectedMotifLevel3Item = React.useMemo(
    () => motifLevel3Items.find(item => item.key === selectedMotifLevel3) || null,
    [motifLevel3Items, selectedMotifLevel3]
  );

  const motifLevel4Items = React.useMemo(() => {
    if (!selectedMotifLevel3Item) return [];
    return selectedMotifLevel3Item.children || [];
  }, [selectedMotifLevel3Item]);

  // Motif level change handlers
  const handleMotifLevel1Change = (e) => {
    const value = e.target.value;
    setSelectedMotifLevel1(value);
    setSelectedMotifLevel2("");
    setSelectedMotifLevel3("");
    setSelectedMotifLevel4("");
  };

  const handleMotifLevel2Change = (e) => {
    const value = e.target.value;
    setSelectedMotifLevel2(value);
    setSelectedMotifLevel3("");
    setSelectedMotifLevel4("");
  };

  const handleMotifLevel3Change = (e) => {
    const value = e.target.value;
    setSelectedMotifLevel3(value);
    setSelectedMotifLevel4("");
  };

  const handleMotifLevel4Change = (e) => {
    const value = e.target.value;
    setSelectedMotifLevel4(value);
  };

  // Auto-select if only one option available for Motif
  React.useEffect(() => {
    if (selectedMotifLevel1 && motifLevel2Items.length === 1 && !selectedMotifLevel2) {
      setSelectedMotifLevel2(motifLevel2Items[0].key);
    }
  }, [selectedMotifLevel1, motifLevel2Items, selectedMotifLevel2]);

  React.useEffect(() => {
    if (selectedMotifLevel2 && motifLevel3Items.length === 1 && !selectedMotifLevel3) {
      setSelectedMotifLevel3(motifLevel3Items[0].key);
    }
  }, [selectedMotifLevel2, motifLevel3Items, selectedMotifLevel3]);

  React.useEffect(() => {
    if (selectedMotifLevel3 && motifLevel4Items.length === 1 && !selectedMotifLevel4) {
      setSelectedMotifLevel4(motifLevel4Items[0].key);
    }
  }, [selectedMotifLevel3, motifLevel4Items, selectedMotifLevel4]);

  // Helper function to get all level 4 items from the selected level
  const getAllLevel4MotifItems = () => {
    if (selectedMotifLevel4) {
      // Level 4 is selected, return that single item
      const item = motifLevel4Items.find(item => item.key === selectedMotifLevel4);
      return item ? [item] : [];
    }
    if (selectedMotifLevel3Item && selectedMotifLevel3Item.children) {
      return selectedMotifLevel3Item.children.filter(item => item.level === 4);
    }
    if (selectedMotifLevel2Item && selectedMotifLevel2Item.children) {
      // Get all level 4 items from all level 3 children
      const allLevel4Items = [];
      selectedMotifLevel2Item.children.forEach(level3 => {
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

  // Helper function to calculate motif code range
  const calculateMotifCodeRange = () => {
    const allLevel4Items = getAllLevel4MotifItems();
    if (allLevel4Items.length === 0) return null;
    const codes = allLevel4Items.map(item => item.code).filter(c => c);
    if (codes.length === 0) return null;
    const min = codes[0];
    const max = codes[codes.length - 1];
    return min === max ? min : `${min}-${max}`;
  };

  // Helper function to build motif path label, skipping "general" at level 3 (aligned with ATU format)
  const buildMotifPathLabel = () => {
    const parts = [];
    if (selectedMotifLevel1Item) parts.push(selectedMotifLevel1Item.name);
    if (selectedMotifLevel2Item) parts.push(selectedMotifLevel2Item.name);
    // Skip level 3 if it's "general" (name is null)
    if (selectedMotifLevel3Item && selectedMotifLevel3Item.name && selectedMotifLevel3Item.name !== "general") {
      parts.push(selectedMotifLevel3Item.name);
    }
    return parts.join(" > ");
  };

  const handleAddMotifFromHierarchy = () => {
    // If level 4 (specific motif) is selected, use that (aligned with ATU format)
    if (selectedMotifLevel4) {
      const motifItem = motifLevel4Items.find(item => item.key === selectedMotifLevel4);
      if (!motifItem) return;

      const pathLabel = buildMotifPathLabel();
      const label = `Motif ${motifItem.code}: ${motifItem.title} (${pathLabel})`;

      const currentTypes = Array.isArray(motif.motif_type)
        ? motif.motif_type
        : (motif.motif_type ? [motif.motif_type] : []);

      if (currentTypes.includes(label)) {
        setSelectedMotifLevel1("");
        setSelectedMotifLevel2("");
        setSelectedMotifLevel3("");
        setSelectedMotifLevel4("");
        return;
      }

      const updatedTypes = [...currentTypes, label];
      setMotif({ ...motif, motif_type: updatedTypes });

      setSelectedMotifLevel1("");
      setSelectedMotifLevel2("");
      setSelectedMotifLevel3("");
      setSelectedMotifLevel4("");
      return;
    }

    // Otherwise, add the most specific selected category level
    const chosen = selectedMotifLevel3Item || selectedMotifLevel2Item || selectedMotifLevel1Item;
    if (!chosen) return;

    const pathLabel = buildMotifPathLabel();

    // If level 4 is not selected, add motif code range (aligned with ATU format)
    let label;
    const range = calculateMotifCodeRange();
    if (range) {
      label = `Motif ${range}: ${pathLabel}`;
    } else {
      label = `Motif Category: ${pathLabel}`;
    }

    const currentTypes = Array.isArray(motif.motif_type)
      ? motif.motif_type
      : (motif.motif_type ? [motif.motif_type] : []);

    if (currentTypes.includes(label)) {
      setSelectedMotifLevel1("");
      setSelectedMotifLevel2("");
      setSelectedMotifLevel3("");
      setSelectedMotifLevel4("");
      return;
    }

    const updatedTypes = [...currentTypes, label];
    setMotif({ ...motif, motif_type: updatedTypes });

    setSelectedMotifLevel1("");
    setSelectedMotifLevel2("");
    setSelectedMotifLevel3("");
    setSelectedMotifLevel4("");
  };

  const handleRemoveMotif = (index) => {
    // Ensure motif_type is an array
    const currentTypes = Array.isArray(motif.motif_type) 
      ? motif.motif_type 
      : (motif.motif_type ? [motif.motif_type] : []);
    const updatedTypes = currentTypes.filter((_, i) => i !== index);
    setMotif({ ...motif, motif_type: updatedTypes });
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

      {/* Motif hierarchical selector (multi-select) - based on CSV */}
      <div style={{ marginTop: "0.75rem" }}>
        <div className="section-header-row">
          <span>Motif Categories (multi-select)</span>
        </div>
        <div className="grid-2" style={{ marginTop: "0.25rem" }}>
          <label>
            Level 1
            <select value={selectedMotifLevel1} onChange={handleMotifLevel1Change}>
              <option value="">– Select Level 1 –</option>
              {motifLevel1Items.map((item, index) => {
                // Thompson Motif Index standard letters: A-Z but skip I and Y
                // A, B, C, D, E, F, G, H, J, K, L, M, N, O, P, Q, R, S, T, U, V, W, X, Z
                const standardLetters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Z'];
                const letter = standardLetters[index] || String.fromCharCode(65 + index);
                return (
                  <option key={item.key} value={item.key}>
                    {letter}. {item.name}
                  </option>
                );
              })}
            </select>
          </label>
          <label>
            Level 2
            <select
              value={selectedMotifLevel2}
              onChange={handleMotifLevel2Change}
              disabled={!selectedMotifLevel1 || motifLevel2Items.length === 0}
            >
              <option value="">– Select Level 2 –</option>
              {motifLevel2Items.map((item) => (
                <option key={item.key} value={item.key}>
                  {item.range}: {item.name}
                </option>
              ))}
            </select>
          </label>
        </div>
        {selectedMotifLevel2 && motifLevel3Items.length > 0 && (
          <div style={{ marginTop: "0.25rem" }}>
            <label>
              Level 3 (optional)
              <select
                value={selectedMotifLevel3}
                onChange={handleMotifLevel3Change}
                disabled={!selectedMotifLevel2}
              >
                <option value="">– Select Level 3 (optional) –</option>
                {motifLevel3Items.map((item) => {
                  const displayName = item.name || "general";
                  return (
                    <option key={item.key} value={item.key}>
                      {displayName}
                    </option>
                  );
                })}
              </select>
            </label>
          </div>
        )}
        {selectedMotifLevel3 && motifLevel4Items.length > 0 && (
          <div style={{ marginTop: "0.25rem" }}>
            <label>
              Level 4 (optional)
              <select
                value={selectedMotifLevel4}
                onChange={handleMotifLevel4Change}
                disabled={!selectedMotifLevel3}
              >
                <option value="">– Select Level 4 (optional) –</option>
                {motifLevel4Items.map((item) => (
                  <option key={item.key} value={item.key}>
                    {item.code}: {item.title}
                  </option>
                ))}
              </select>
            </label>
          </div>
        )}
        {(selectedMotifLevel1 || selectedMotifLevel2 || selectedMotifLevel3 || selectedMotifLevel4) && (
          <button
            type="button"
            className="ghost-btn"
            onClick={handleAddMotifFromHierarchy}
            style={{ marginTop: "0.5rem" }}
          >
            + Add Selected Motif
          </button>
        )}
      </div>

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

