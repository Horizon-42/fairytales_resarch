import React from "react";
import CreatableSelect from 'react-select/creatable';
import { CHARACTER_ARCHETYPES, HELPER_TYPES, HELPER_TYPE_DISPLAY_NAMES } from "../constants.js";
import { HIGHLIGHT_COLORS, customSelectStyles } from "../utils/helpers.js";

export default function CharacterSection({ 
  motif, 
  setMotif, 
  highlightedChars, 
  setHighlightedChars,
  newlyCreatedCharacterIndex,
  setNewlyCreatedCharacterIndex,
  onAutoAnnotateCharacters,
  autoAnnotateCharactersLoading
}) {
  // State for annotation mode selection
  const [annotationMode, setAnnotationMode] = React.useState("recreate");
  const characters = Array.isArray(motif.character_archetypes)
    ? motif.character_archetypes
    : [];

  const isLegacyFormat =
    characters.length > 0 && typeof characters[0] === "string";

  const safeCharacters = isLegacyFormat
    ? characters.map((c) => ({ name: "", alias: "", archetype: c }))
    : characters;

  // Create character options for obstacle thrower selector
  const characterOptions = safeCharacters
    .filter(char => char.name && char.name.trim())
    .map(char => ({
      label: char.name,
      value: char.name
    }));

  // Refs for character input fields
  const characterInputRefs = React.useRef({});

  // Auto-focus to newly created character
  React.useEffect(() => {
    if (newlyCreatedCharacterIndex != null && characterInputRefs.current[newlyCreatedCharacterIndex]) {
      const input = characterInputRefs.current[newlyCreatedCharacterIndex];
      setTimeout(() => {
        input.focus();
        input.select(); // Select the text so user can easily replace it
        if (setNewlyCreatedCharacterIndex) {
          setNewlyCreatedCharacterIndex(null); // Clear the flag
        }
      }, 100);
    }
  }, [newlyCreatedCharacterIndex, setNewlyCreatedCharacterIndex]);

  const handleCharacterChange = (index, field, value) => {
    const next = [...safeCharacters];
    next[index] = { ...next[index], [field]: value };
    setMotif({ ...motif, character_archetypes: next });
  };

  const addCharacter = () => {
    setMotif({
      ...motif,
      character_archetypes: [
        ...safeCharacters,
        { name: "", alias: "", archetype: "" }
      ]
    });
  };

  const removeCharacter = (index) => {
    const next = safeCharacters.filter((_, i) => i !== index);
    setMotif({ ...motif, character_archetypes: next });
  };

  const toggleHighlight = (char) => {
    if (!setHighlightedChars) return;
    const name = (char.name || "").trim();
    if (!name) return;

    setHighlightedChars(prev => {
      const next = { ...prev };
      if (next[name]) {
        delete next[name];
      } else {
        const usedColors = Object.values(next);
        let color = HIGHLIGHT_COLORS.find(c => !usedColors.includes(c));
        if (!color) {
          color = HIGHLIGHT_COLORS[Object.keys(next).length % HIGHLIGHT_COLORS.length];
        }
        next[name] = color;
      }
      return next;
    });
  };

  const isHighlighted = (char) => {
    const name = (char.name || "").trim();
    return highlightedChars && !!highlightedChars[name];
  };

  const getHighlightColor = (char) => {
    const name = (char.name || "").trim();
    return highlightedChars ? highlightedChars[name] : null;
  };

  // Handle obstacle thrower change (convert between string and array for backward compatibility)
  const handleObstacleThrowerChange = (selectedOptions) => {
    const values = selectedOptions ? selectedOptions.map(opt => opt.value) : [];
    setMotif({ ...motif, obstacle_thrower: values });
  };

  // Get current obstacle thrower value (handle both string and array formats)
  const getObstacleThrowerValue = () => {
    const obstacleThrower = motif.obstacle_thrower;
    if (!obstacleThrower) return [];
    
    // If it's already an array, use it
    if (Array.isArray(obstacleThrower)) {
      return obstacleThrower.map(name => ({
        label: name,
        value: name
      }));
    }
    
    // If it's a string (legacy format), convert to array
    if (typeof obstacleThrower === 'string' && obstacleThrower.trim()) {
      return [{
        label: obstacleThrower,
        value: obstacleThrower
      }];
    }
    
    return [];
  };

  // Handle helper type change (convert between string and array for backward compatibility)
  const handleHelperTypeChange = (selectedOptions) => {
    const values = selectedOptions ? selectedOptions.map(opt => opt.value) : [];
    setMotif({ ...motif, helper_type: values });
  };

  // Get current helper type value (handle both string and array formats)
  const getHelperTypeValue = () => {
    const helperType = motif.helper_type;
    if (!helperType) return [];
    
    // If it's already an array, use it
    if (Array.isArray(helperType)) {
      return helperType.map(type => ({
        label: HELPER_TYPE_DISPLAY_NAMES[type] || type,
        value: type
      }));
    }
    
    // If it's a string (legacy format), convert to array
    if (typeof helperType === 'string' && helperType.trim()) {
      // Check if it's a valid helper type code
      if (HELPER_TYPES.includes(helperType)) {
        return [{
          label: HELPER_TYPE_DISPLAY_NAMES[helperType] || helperType,
          value: helperType
        }];
      }
      // If it's not a valid code, treat it as a custom value
      return [{
        label: helperType,
        value: helperType
      }];
    }
    
    return [];
  };

  // Create helper type options
  const helperTypeOptions = HELPER_TYPES.map(type => ({
    label: HELPER_TYPE_DISPLAY_NAMES[type] || type,
    value: type
  }));

  return (
    <section className="card">
      <h2>Characters</h2>
      <div className="section-header-row">
        <span>Story Characters</span>
        {typeof onAutoAnnotateCharacters === "function" && (
          <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
            <select
              value={annotationMode}
              onChange={(e) => setAnnotationMode(e.target.value)}
              disabled={!!autoAnnotateCharactersLoading}
              style={{
                padding: "0.4rem 0.5rem",
                fontSize: "0.8rem",
                lineHeight: "1.2",
                border: "1px solid #cbd5e1",
                borderRadius: "6px",
                backgroundColor: "white",
                cursor: autoAnnotateCharactersLoading ? "not-allowed" : "pointer",
                marginBottom: 0,
                width: "auto",
                minWidth: "110px",
                height: "32px",
                boxSizing: "border-box",
                appearance: "none",
                WebkitAppearance: "none",
                MozAppearance: "none"
              }}
              title="Select annotation mode: Supplement (add missing), Modify (update existing), or Recreate (from scratch)"
            >
              <option value="recreate">Recreate</option>
              <option value="supplement">Supplement</option>
              <option value="modify">Modify</option>
            </select>
            <button
              type="button"
              className="ghost-btn"
              onClick={() => onAutoAnnotateCharacters(annotationMode)}
              disabled={!!autoAnnotateCharactersLoading}
              title="Auto-fill characters, helper types, and obstacle throwers using the LLM backend"
              style={{ minWidth: "100px", whiteSpace: "nowrap", height: "32px" }}
            >
              {autoAnnotateCharactersLoading ? "Annotating…" : "Auto-fill"}
            </button>
          </div>
        )}
      </div>

      {safeCharacters.length === 0 && (
        <p className="hint">
          No characters defined. Add characters to link specific names to
          archetypes.
        </p>
      )}

      {safeCharacters.map((char, idx) => {
        const active = isHighlighted(char);
        const color = getHighlightColor(char);
        
        return (
          <div key={idx} className="propp-row">
            <div className="grid-3">
              <label>
                Name
                <input
                  ref={(el) => {
                    if (el) {
                      characterInputRefs.current[idx] = el;
                    }
                  }}
                  value={char.name}
                  onChange={(e) => handleCharacterChange(idx, "name", e.target.value)}
                  placeholder="e.g. Aladdin"
                />
              </label>
              <label>
                Alias (Optional)
                <input
                  value={char.alias}
                  onChange={(e) => handleCharacterChange(idx, "alias", e.target.value)}
                  placeholder="e.g. Street Rat; Boy"
                />
              </label>
              <label>
                Archetype
                <select
                  value={char.archetype}
                  onChange={(e) =>
                    handleCharacterChange(idx, "archetype", e.target.value)
                  }
                >
                  <option value="">– Select –</option>
                  {CHARACTER_ARCHETYPES.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <div style={{ display: 'flex', gap: '0.5rem', marginTop: "0.25rem" }}>
              <button
                type="button"
                className={`ghost-btn ${active ? "active-highlight" : ""}`}
                style={active ? { background: color, borderColor: "#ccc", color: "#000", fontWeight: "bold" } : {}}
                onClick={() => toggleHighlight(char)}
              >
                {active ? "Unhighlight" : "Highlight"}
              </button>
              <button
                type="button"
                className="ghost-btn"
                style={{ color: "#ef4444", borderColor: "#ef4444" }}
                onClick={() => removeCharacter(idx)}
              >
                Remove
              </button>
            </div>
          </div>
        );
      })}

      <button type="button" className="ghost-btn" onClick={addCharacter} style={{ marginTop: "1rem" }}>
        + Add Character
      </button>

      <hr />

      <div className="grid-2">
        <label>
          Helper type
          <CreatableSelect
            isMulti
            options={helperTypeOptions}
            value={getHelperTypeValue()}
            onChange={handleHelperTypeChange}
            placeholder="Select or create helper types..."
            styles={customSelectStyles}
          />
        </label>
        <label>
          Obstacle thrower
          <CreatableSelect
            isMulti
            options={characterOptions}
            value={getObstacleThrowerValue()}
            onChange={handleObstacleThrowerChange}
            placeholder="Select or create obstacle throwers..."
            styles={customSelectStyles}
          />
        </label>
      </div>
    </section>
  );
}

