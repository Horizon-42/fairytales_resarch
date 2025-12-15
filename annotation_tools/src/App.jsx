import React, { useMemo, useState, useEffect, useRef } from "react";
import CreatableSelect from 'react-select/creatable';
import {
  ATU_TYPES,
  CHARACTER_ARCHETYPES,
  VALUE_TYPES,
  ENDING_TYPES,
  PROPP_FUNCTIONS,
  TARGET_CATEGORIES,
  OBJECT_TYPES
} from "./constants.js";
import { organizeFiles, mapV1ToState, mapV2ToState, generateUUID } from "./utils/fileHandler.js";

function multiSelectFromEvent(e) {
  return Array.from(e.target.selectedOptions).map((o) => o.value);
}

function downloadJson(filename, data) {
  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: "application/json"
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

// distinct pastel-like colors for highlighting
const HIGHLIGHT_COLORS = [
  "#fef08a", // yellow
  "#bbf7d0", // green
  "#bfdbfe", // blue
  "#fbcfe8", // pink
  "#ddd6fe", // indigo
  "#fed7aa", // orange
  "#99f6e4", // teal
  "#e9d5ff", // violet
  "#fecaca", // red-ish
  "#a5f3fc"  // cyan
];

const emptyProppFn = () => ({
  id: generateUUID(),
  fn: "",
  spanType: "paragraph", // "paragraph" or "text"
  span: { start: 0, end: 0 }, // For paragraphs
  textSpan: { start: 0, end: 0, text: "" }, // For raw text index
  evidence: "",
  narrative_event_id: null
});

const customStyles = {
  container: (base) => ({ ...base, marginTop: '4px' }),
  multiValueLabel: (base) => ({
    ...base,
    fontSize: '100%',
    padding: '2px 4px'
  }),
  multiValue: (base) => ({
    ...base,
    padding: '2px'
  })
};

export default function App() {
  const [storyFiles, setStoryFiles] = useState([]);
  const [v1JsonFiles, setV1JsonFiles] = useState({});
  const [v2JsonFiles, setV2JsonFiles] = useState({});
  const [selectedStoryIndex, setSelectedStoryIndex] = useState(-1);
  const [currentSelection, setCurrentSelection] = useState(null);

  const [jsonSaveHint, setJsonSaveHint] = useState(
    "datasets/iron/persian/persian/json/FA_XXX.json"
  );
  const [showPreview, setShowPreview] = useState(false);

  const [id, setId] = useState("FA_XXX");
  const [culture, setCulture] = useState("Persian");
  const [title, setTitle] = useState("");

  const [sourceText, setSourceText] = useState({
    text: "",
    language: "en",
    type: "summary",
    reference_uri: ""
  });

  const [annotationLevel, setAnnotationLevel] = useState("Deep");

  const [meta, setMeta] = useState({
    main_motif: "",
    atu_type: "",
    ending_type: "HAPPY_REUNION",
    key_values: [],
    target_motif: true
  });

  const [motif, setMotif] = useState({
    atu_type: "",
    character_archetypes: [],
    obstacle_pattern: [],
    obstacle_thrower: "",
    helper_type: "",
    thinking_process: ""
  });

  const [paragraphSummaries, setParagraphSummaries] = useState({
    perParagraph: {},   // { [paraIndex]: summaryText }
    combined: [],       // [{ start_para, end_para, text }]
    whole: ""           // whole story summary
  });
  const [proppFns, setProppFns] = useState([emptyProppFn()]);
  const [proppNotes, setProppNotes] = useState("");

  const [deepMeta, setDeepMeta] = useState({
    ending_type: "HAPPY_REUNION",
    key_values: []
  });

  const [narrativeStructure, setNarrativeStructure] = useState([""]);

  const [crossValidation, setCrossValidation] = useState({
    shared_story: null,
    bias_reflection: {
      cultural_reading: "",
      gender_norms: "",
      hero_villain_mapping: "",
      ambiguous_motifs: []
    }
  });

  const [qa, setQa] = useState({
    annotator: "",
    date_annotated: "",
    confidence: 0.8,
    notes: ""
  });

  const [persianSource, setPersianSource] = useState({
    text: "",
    language: "fa",
    type: "excerpt",
    reference_uri: ""
  });

  const jsonV1 = useMemo(
    () => ({
      id,
      culture,
      title,
      source_text: sourceText,
      annotation_level: annotationLevel,
      metadata: meta,
      thinking_process: motif.thinking_process || "",
      annotation: {
        motif,
        deep: {
          paragraph_summaries: {
            per_paragraph: paragraphSummaries.perParagraph || {},
            combined: (paragraphSummaries.combined || []).filter(c => c.text && c.text.trim()),
            whole: paragraphSummaries.whole || ""
          },
          propp_functions: proppFns.filter((f) => f.fn || f.evidence),
          propp_notes: proppNotes
        },
        meta: deepMeta
      },
      narrative_structure: narrativeStructure.filter(
        (n) => (typeof n === "string" ? n.trim() : n.event_type)
      ),
      cross_validation: crossValidation,
      qa,
      source_text_persian: persianSource
    }),
    [
      id,
      culture,
      title,
      sourceText,
      annotationLevel,
      meta,
      motif,
      paragraphSummaries,
      proppFns,
      proppNotes,
      deepMeta,
      narrativeStructure,
      crossValidation,
      qa,
      persianSource
    ]
  );

  const jsonV2 = useMemo(() => {
    // Extract characters safely
    const characters = Array.isArray(motif.character_archetypes)
      ? motif.character_archetypes.map((c) =>
          typeof c === "string" ? { name: "", alias: "", archetype: c } : c
        )
      : [];

    return {
      version: "2.0",
      metadata: {
        id,
        title,
        culture,
        annotator: qa.annotator,
        date_annotated: qa.date_annotated,
        confidence: qa.confidence,
        annotation_level: annotationLevel
      },
      source_info: {
        language: sourceText.language,
        type: sourceText.type,
        reference_uri: sourceText.reference_uri,
        text_content: sourceText.text // Optional: include full text?
      },
      characters: characters,
      narrative_events: narrativeStructure.map((n) =>
        typeof n === "string"
          ? { event_type: "OTHER", description: n }
          : n
      ),
      themes_and_motifs: {
        atu_type: meta.atu_type,
        atu_description: meta.main_motif,
        ending_type: meta.ending_type,
        key_values: meta.key_values,
        obstacle_pattern: motif.obstacle_pattern,
        obstacle_thrower: motif.obstacle_thrower,
        helper_type: motif.helper_type,
        thinking_process: motif.thinking_process
      },
      analysis: {
        propp_functions: proppFns.filter((f) => f.fn || f.evidence),
        propp_notes: proppNotes,
        paragraph_summaries: {
          per_paragraph: paragraphSummaries.perParagraph || {},
          combined: (paragraphSummaries.combined || []).filter(c => c.text && c.text.trim()),
          whole: paragraphSummaries.whole || ""
        },
        bias_reflection: crossValidation.bias_reflection,
        qa_notes: qa.notes
      }
    };
  }, [
    jsonV1 // Depend on V1 inputs implicitly or just list them all. 
           // For simplicity, reusing same deps as V1 would be better, 
           // but I'll trust React re-renders or list deps if needed.
           // Actually, let's just list the same deps to be safe.
  , id, culture, title, sourceText, annotationLevel, meta, motif, paragraphSummaries, proppFns, proppNotes, deepMeta, narrativeStructure, crossValidation, qa, persianSource]);

  const [previewVersion, setPreviewVersion] = useState("v2");

  const handleSave = async (version, silent = false) => {
    // Determine content and suffix
    const data = version === "v2" ? jsonV2 : jsonV1;
    
    // We need the original file path to determine where to save.
    // The currently selected story file object has `webkitRelativePath` or `path` property.
    // In handleStoryFilesChange we store: { file, name, path: relPath, text }
    const currentStory = storyFiles[selectedStoryIndex];
    
    if (!currentStory) {
      if (!silent) alert("No story selected to save.");
      return;
    }

    try {
      const response = await fetch("http://localhost:3001/api/save", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          originalPath: currentStory.path,
          content: data,
          version: version
        })
      });

      const result = await response.json();
      if (response.ok) {
        if (!silent) alert(`Saved successfully to: ${result.path}`);
        console.log(`Auto-save (${version}) success: ${result.path}`);
        setLastAutoSave(new Date());
      } else {
        if (!silent) alert(`Failed to save: ${result.error}`);
        console.error(`Auto-save (${version}) failed: ${result.error}`);
        // Fallback to download if server fails and not silent (or silent? maybe not download on auto-save)
        if (!silent) downloadJson(`${id}_${version}.json`, data);
      }
    } catch (err) {
      console.error("Save failed, falling back to download", err);
      // Fallback to download
      const suffix = version === "v2" ? "_v2" : "_v1";
      if (!silent) downloadJson(`${id}${suffix}.json`, data);
    }
  };

  // Auto-save logic
  const saveRef = useRef(handleSave);
  
  // Keep ref current
  useEffect(() => {
    saveRef.current = handleSave;
  });

  useEffect(() => {
    const interval = setInterval(() => {
      // Only auto-save if a story is selected
      if (selectedStoryIndex !== -1) {
        console.log("Triggering auto-save...");
        // Save both versions silently
        saveRef.current("v1", true);
        saveRef.current("v2", true);
      }
    }, 5 * 60 * 1000); // 5 minutes

    return () => clearInterval(interval);
  }, [selectedStoryIndex]); // Reset timer if story changes? Or just keep running?
  // If we want consistent 5 min intervals regardless of story change, remove dependency.
  // But if story changes, we probably want to restart timer or just let it tick.
  // Given we check `selectedStoryIndex` inside, it's safe. 
  // Dependency on selectedStoryIndex in useEffect ensures we don't save the WRONG story if index changes mid-tick?
  // No, the ref `saveRef` always has the CURRENT closure which captures the CURRENT selectedStoryIndex (via state in handleSave).
  // Wait, `handleSave` closes over `selectedStoryIndex`. 
  // So `saveRef.current` (which is updated every render) will always have the fresh `handleSave` which has the fresh index.
  // So we don't strictly need `selectedStoryIndex` in dependency array for correctness of DATA, 
  // but we might want to reset the timer when switching stories so we don't auto-save immediately after opening a new one.
  // Let's reset on story change.

  const loadState = (loaded) => {
    if (loaded.id) setId(loaded.id);
    if (loaded.culture) setCulture(loaded.culture);
    if (loaded.title) setTitle(loaded.title);
    if (loaded.annotationLevel) setAnnotationLevel(loaded.annotationLevel);
    
    setMeta(prev => ({ ...prev, ...loaded.meta }));
    setMotif(prev => ({ ...prev, ...loaded.motif }));
    
    if (loaded.paragraphSummaries) {
      // Handle different formats
      if (Array.isArray(loaded.paragraphSummaries)) {
        // Legacy: convert array to new structure
        const perParagraph = {};
        loaded.paragraphSummaries.forEach((item, i) => {
          if (typeof item === "string" && item.trim()) {
            perParagraph[i] = item;
          } else if (item && item.text && item.text.trim()) {
            // Was combined format before, keep as combined? Or map to per-paragraph?
            // If start_para === end_para, it's per-paragraph
            if (item.start_para === item.end_para) {
              perParagraph[item.start_para] = item.text;
            }
          }
        });
        // Extract combined items (multi-paragraph ranges)
        const combined = loaded.paragraphSummaries
          .filter(item => item && typeof item === "object" && item.start_para !== item.end_para)
          .map(item => ({ start_para: item.start_para, end_para: item.end_para, text: item.text }));

        setParagraphSummaries({ perParagraph, combined, whole: "" });
      } else if (typeof loaded.paragraphSummaries === "object") {
        // New structure
        setParagraphSummaries({
          perParagraph: loaded.paragraphSummaries.perParagraph || {},
          combined: loaded.paragraphSummaries.combined || [],
          whole: loaded.paragraphSummaries.whole || ""
        });
      }
    }
    if (loaded.proppFns) setProppFns(loaded.proppFns);
    if (loaded.proppNotes) setProppNotes(loaded.proppNotes);
    if (loaded.deepMeta) setDeepMeta(prev => ({ ...prev, ...loaded.deepMeta }));
    
    if (loaded.narrativeStructure) setNarrativeStructure(loaded.narrativeStructure);
    
    if (loaded.crossValidation) setCrossValidation(prev => ({ ...prev, ...loaded.crossValidation }));
    if (loaded.qa) setQa(prev => ({ ...prev, ...loaded.qa }));
    
    // Check deep fields from V1 map if not covered
    if (loaded.proppFns) setProppFns(loaded.proppFns);
  };

  const resetState = () => {
    setTitle("");
    setMeta({
      main_motif: "",
      atu_type: "",
      ending_type: "HAPPY_REUNION",
      key_values: [],
      target_motif: true
    });
    setMotif({
      atu_type: "",
      character_archetypes: [],
      obstacle_pattern: [],
      obstacle_thrower: "",
      helper_type: "",
      thinking_process: ""
    });
    setParagraphSummaries({
      perParagraph: {},
      combined: [],
      whole: ""
    });
    setProppFns([emptyProppFn()]);
    setProppNotes("");
    setDeepMeta({ ending_type: "HAPPY_REUNION", key_values: [] });
    setNarrativeStructure([""]);
    setCrossValidation({
      shared_story: null,
      bias_reflection: {
        cultural_reading: "",
        gender_norms: "",
        hero_villain_mapping: "",
        ambiguous_motifs: []
      }
    });
    setQa({
      annotator: "",
      date_annotated: new Date().toISOString().split("T")[0],
      confidence: 0.8,
      notes: ""
    });
  };

  const handleStoryFilesChange = async (event) => {
    const files = event.target.files;
    if (!files) return;

    // Use utility to organize files
    const { texts, v1Jsons, v2Jsons } = organizeFiles(files);
    
    // Sort texts alphabetically
    texts.sort((a, b) => a.id.localeCompare(b.id, undefined, { numeric: true, sensitivity: 'base' }));

    // Read text content for all text files (so we can display them)
    // For large datasets, we might want to do this lazily, but user asked for "story content".
    // We'll stick to pre-loading texts for now as per previous logic, but maybe optimize if needed.
    const withContent = await Promise.all(
      texts.map(async (t) => {
        const textRaw = await t.file.text();
        // Normalize line endings to ensure index consistency
        const text = textRaw.replace(/\r\n/g, '\n');
        return { ...t, name: t.file.name, text };
      })
    );

    setStoryFiles(withContent);
    setV1JsonFiles(v1Jsons);
    setV2JsonFiles(v2Jsons);

    if (withContent.length > 0) {
      // Select first story
      // We can't call handleSelectStory directly because state updates (files) are async/batched.
      // We have to explicitly pass the new data or use an effect.
      // Let's call a helper with the data.
      selectStoryWithData(0, withContent, v1Jsons, v2Jsons);
    }
  };

  const selectStoryWithData = async (index, texts, v1Map, v2Map) => {
    setSelectedStoryIndex(index);
    const story = texts[index];
    if (!story) return;

    // Default setup from text file
    const idGuess = story.id; // derived in organizeFiles
    setId(idGuess);
    setSourceText((prev) => ({
      ...prev,
      text: story.text,
      reference_uri: `file://${relPathToDatasetHint(story.path)}`
    }));

    // Reset annotations first
    resetState();
    setHighlightedRanges({});
    setHighlightedChars({});

    // Check for existing JSON
    // Priority 1: Check server (disk) for latest version
    try {
      const response = await fetch("http://localhost:3001/api/load", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ originalPath: story.path })
      });
      
      const result = await response.json();
      if (result.found && result.content) {
        console.log(`Loaded ${result.version === 2 ? "V2" : "V1"} from server: ${result.path}`, result.content);
        const mappedState = result.version === 2 ? mapV2ToState(result.content) : mapV1ToState(result.content);
        console.log("Mapped State:", mappedState);
        loadState(mappedState);
        return; // Stop here if server found it
      }
    } catch (err) {
      console.warn("Server load failed, falling back to browser memory files", err);
    }

    // Priority 2: Browser memory (from initial folder upload)
    let jsonFile = v2Map[idGuess];
    let version = 2;
    
    if (!jsonFile) {
      jsonFile = v1Map[idGuess];
      version = 1;
    }

    if (jsonFile) {
      try {
        const content = await jsonFile.text();
        const data = JSON.parse(content);
        const mappedState = version === 2 ? mapV2ToState(data) : mapV1ToState(data);
        loadState(mappedState);
      } catch (err) {
        console.error("Failed to load JSON annotation from memory", err);
      }
    }
  };

  const handleSelectStory = (index) => {
    selectStoryWithData(index, storyFiles, v1JsonFiles, v2JsonFiles);
  };

  const handleStorySelection = () => {
    const selection = window.getSelection();
    if (!selection.rangeCount || selection.isCollapsed) {
      setCurrentSelection(null);
      return;
    }

    const range = selection.getRangeAt(0);
    const container = document.getElementById("story-content-pre");
    
    if (!container || !container.contains(range.commonAncestorContainer)) {
      return;
    }

    // Calculate offset relative to the pre container
    // This assumes the pre contains a single text node, which is true for our app
    // If not, we'd need a more complex walker.
    // For now, let's assume simple structure.
    
    // Actually, create a range from start of container to start of selection
    const preRange = range.cloneRange();
    preRange.selectNodeContents(container);
    preRange.setEnd(range.startContainer, range.startOffset);
    const start = preRange.toString().length;
    const end = start + range.toString().length;
    const text = range.toString();

    setCurrentSelection({ start, end, text });
  };

  const [activeTab, setActiveTab] = useState("characters");
  // Map of character name -> color string
  const [highlightedChars, setHighlightedChars] = useState({});
  const [highlightedRanges, setHighlightedRanges] = useState({}); // { [uuid]: { start, end, color } }
  const [lastAutoSave, setLastAutoSave] = useState(null);

  // Scroll to summary focus
  useEffect(() => {
    const focusHighlight = highlightedRanges["summary-focus"];
    if (focusHighlight) {
      // Allow DOM to update
      setTimeout(() => {
        const el = document.getElementById("summary-focus-mark");
        if (el) {
          el.scrollIntoView({ behavior: "smooth", block: "center" });
        }
      }, 100);
    }
  }, [highlightedRanges]);

  const onAddProppFn = (newEvent) => {
    // Only add if event_type is not empty and not "OTHER"
    if (!newEvent.event_type || newEvent.event_type === "OTHER") return;

    setProppFns((prev) => {
      // Check if we already have a Propp function linked to this narrative ID
      const existingIndex = prev.findIndex(p => p.narrative_event_id === newEvent.id);

      if (existingIndex >= 0) {
        // Update existing
        const next = [...prev];
        next[existingIndex] = {
          ...next[existingIndex],
          fn: newEvent.event_type,
          // Optional: update evidence/textSpan too if user changed it in Narrative tab?
          // If we want tight coupling, yes.
          textSpan: newEvent.text_span || next[existingIndex].textSpan,
          evidence: newEvent.description || next[existingIndex].evidence
        };
        return next;
      } else {
        // Create new
        return [
          ...prev,
          {
            id: generateUUID(),
            fn: newEvent.event_type,
            spanType: "text",
            span: { start: 0, end: 0 },
            textSpan: newEvent.text_span || { start: 0, end: 0, text: "" },
            evidence: newEvent.description || "",
            narrative_event_id: newEvent.id
          }
        ];
      }
    });
  };

  const handleSyncPropp = () => {
    // 1. Identify all valid narrative events
    const validNarratives = narrativeStructure.filter(n =>
      n.id && n.event_type && n.event_type !== "OTHER"
    );

    setProppFns(prev => {
      const next = [...prev];

      validNarratives.forEach(narrative => {
        // Check if propp fn exists for this narrative ID
        const existingIdx = next.findIndex(p => p.narrative_event_id === narrative.id);

        if (existingIdx === -1) {
          // Create new
          next.push({
            id: generateUUID(),
            fn: narrative.event_type,
            spanType: "text",
            span: { start: 0, end: 0 },
            textSpan: narrative.text_span || { start: 0, end: 0, text: "" },
            evidence: narrative.description || "",
            narrative_event_id: narrative.id
          });
        } else {
          // Update existing (sync) - Optional: only if empty? 
          // User said "regenerate to create all propps from narrative".
          // Assuming we should sync types.
          const existing = next[existingIdx];
          next[existingIdx] = {
            ...existing,
            fn: narrative.event_type,
            // Sync text span/evidence if they are empty in Propp? Or always override?
            // Safer to only fill if empty or if we want tight sync.
            // Let's assume sync means "make it match narrative".
            textSpan: narrative.text_span || existing.textSpan,
            evidence: narrative.description || existing.evidence
          };
        }
      });

      return next;
    });
  };

  const handleDeleteOrphanPropps = () => {
    setProppFns(prev => {
      // Keep propps that:
      // 1. Have no narrative_event_id (manual ones, though user said "without a narrative", maybe manual ones should be kept or deleted?
      //    "delete button for all propps without a narrative" likely means "orphaned ones" OR "all manual ones".
      //    Let's assume "orphaned" = has narrative_event_id but that ID is not in narrativeStructure.
      //    AND "without narrative" = narrative_event_id is null.
      //    If the goal is "better tracking", we probably only want linked ones.
      //    Let's delete IF (narrative_event_id IS NULL) OR (narrative_event_id NOT IN narrativeStructure).

      const validNarrativeIds = new Set(narrativeStructure.map(n => n.id).filter(Boolean));

      return prev.filter(p => {
        if (!p.narrative_event_id) return false; // Delete manual/unlinked
        return validNarrativeIds.has(p.narrative_event_id); // Keep only if linked exists
      });
    });
  };

  return (
    <div className="app-root">
      <header className="app-header">
        <div className="header-left">
          <span className="logo-icon">✨</span>
          <div>
            <h1>Fairy Tale Annotation Tool</h1>
            <p>
              Aligns with the Persian JSON schema in{" "}
              <code>datasets/iron/persian/persian/json</code>.
            </p>
          </div>
        </div>
        <div className="header-actions">
          <button
            type="button"
            className="ghost-btn"
            onClick={() => setShowPreview((v) => !v)}
          >
            {showPreview ? "Hide JSON" : "Show JSON"}
          </button>
          <div className="save-hint">
            <span className="save-hint-label">Intended JSON path:</span>
            <input
              className="save-hint-input"
              value={jsonSaveHint}
              onChange={(e) => setJsonSaveHint(e.target.value)}
            />
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: "center" }}>
            {lastAutoSave && (
              <span style={{ fontSize: "0.75rem", color: "#6b7280", marginRight: "0.5rem" }}>
                Saved: {lastAutoSave.toLocaleTimeString()}
              </span>
            )}
            <button className="primary-btn" onClick={() => handleSave("v1")}>
              Save V1
            </button>
            <button className="primary-btn" onClick={() => handleSave("v2")}>
              Save V2
            </button>
          </div>
        </div>
      </header>

      <main className="layout">
        <aside className="sidebar">
          <StoryBrowserSection
            storyFiles={storyFiles}
            selectedIndex={selectedStoryIndex}
            selectedStory={storyFiles[selectedStoryIndex]}
            onFilesChange={handleStoryFilesChange}
            onSelectStory={handleSelectStory}
            culture={culture}
            onCultureChange={setCulture}
          />
        </aside>

        <section className="story-stage">
          <div className="story-stage-content">
            {storyFiles[selectedStoryIndex] ? (
              <>
                <h2 className="story-title-display">
                  {storyFiles[selectedStoryIndex].name}
                </h2>
                <div className="story-text-display" onMouseUp={handleStorySelection}>
                  <pre id="story-content-pre">
                    {(() => {
                      const text = storyFiles[selectedStoryIndex].text;
                      
                      // Build a map of term -> color
                      // We need to handle overlap? For now, first match wins or longest wins.
                      const termMap = {};
                      const allTerms = [];
                      
                      // Collect all terms from highlighted characters
                      const motifChars = motif.character_archetypes || [];
                      
                      Object.entries(highlightedChars).forEach(([charName, color]) => {
                        // Find the character data to get aliases
                        const charData = motifChars.find(c => (c.name || "").trim() === charName);
                        if (!charData) return; // Should not happen if sync is good
                        
                        const names = [charData.name];
                        if (charData.alias) {
                          names.push(...charData.alias.split(/;|；/).map(s => s.trim()));
                        }
                        
                        names.filter(n => n).forEach(term => {
                          const lower = term.toLowerCase();
                          // If term already exists, we might overwrite. Longest usually preferred in regex.
                          // Store color for this term
                          termMap[lower] = color;
                          allTerms.push(term);
                        });
                      });

                      // Sort by length descending to match longest terms first
                      allTerms.sort((a, b) => b.length - a.length);
                      
                      const allHighlights = [];

                      // 1. Term matches
                      if (allTerms.length > 0) {
                        const escapedTerms = allTerms.map(t => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
                        const regex = new RegExp(`(${escapedTerms.join("|")})`, "gi");
                        let match;
                        while ((match = regex.exec(text)) !== null) {
                          const term = match[0];
                          const start = match.index;
                          const end = start + term.length;
                          const color = termMap[term.toLowerCase()];
                          if (color) { // Ensure color exists
                            allHighlights.push({ start, end, color, priority: 1 });
                          }
                        }
                      }
                      
                      // 2. Explicit ranges
                      // Important: Ensure highlightedRanges is actually populated
                      if (highlightedRanges) {
                        Object.entries(highlightedRanges).forEach(([key, r]) => {
                          if (r && typeof r.start === 'number' && typeof r.end === 'number') {
                            allHighlights.push({ ...r, id: key, priority: 2 });
                          }
                        });
                      }
                      
                      if (!allHighlights.length) return text;

                      // Sort by start position
                      allHighlights.sort((a, b) => a.start - b.start);

                      // Simple slicing: just use boundaries. 
                      // For overlapping, we'll just let the "last added" highlight take precedence for that segment?
                      // Or we can try to merge.
                      // Let's do a simple approach: split text by ALL boundary points.

                      const boundaries = new Set([0, text.length]);
                      allHighlights.forEach(h => {
                        boundaries.add(h.start);
                        boundaries.add(h.end);
                      });
                      const sortedBoundaries = Array.from(boundaries).sort((a, b) => a - b);

                      const segments = [];
                      for (let i = 0; i < sortedBoundaries.length - 1; i++) {
                        const p1 = sortedBoundaries[i];
                        const p2 = sortedBoundaries[i + 1];
                        if (p1 >= p2) continue;

                        const segmentText = text.slice(p1, p2);

                        // Find active highlight for this segment
                        // We take the highlight that covers this segment with highest priority (or just any)
                        // A highlight covers [p1, p2] if highlight.start <= p1 && highlight.end >= p2

                        const active = allHighlights
                          .filter(h => h.start <= p1 && h.end >= p2)
                          .sort((a, b) => b.priority - a.priority); // Higher priority first

                        const topHighlight = active[0];

                        if (topHighlight) {
                          segments.push(
                            <mark 
                              key={i}
                              id={topHighlight.id === "summary-focus" ? "summary-focus-mark" : undefined}
                              className="highlighted-text"
                              style={{ backgroundColor: topHighlight.color, color: "#000", borderRadius: "2px", padding: "0 2px" }}
                            >
                              {segmentText}
                            </mark>
                          );
                        } else {
                          segments.push(segmentText);
                        }
                      }

                      return segments;
                    })()}
                  </pre>
                </div>
              </>
            ) : (
              <div className="empty-state">
                <p>Select a story from the sidebar to begin reading.</p>
              </div>
            )}
          </div>
        </section>

        <aside className="inspector-pane">
          <div className="inspector-tabs">
            <button
              className={`tab-btn ${activeTab === "characters" ? "active" : ""}`}
              onClick={() => setActiveTab("characters")}
            >
              Characters
            </button>
            <button
              className={`tab-btn ${activeTab === "narrative" ? "active" : ""}`}
              onClick={() => setActiveTab("narrative")}
            >
              Narrative
            </button>
            <button
              className={`tab-btn ${activeTab === "propp" ? "active" : ""}`}
              onClick={() => setActiveTab("propp")}
            >
              Propp
            </button>
            <button
              className={`tab-btn ${activeTab === "summaries" ? "active" : ""}`}
              onClick={() => setActiveTab("summaries")}
            >
              Summaries
            </button>
            <button
              className={`tab-btn ${activeTab === "motifs" ? "active" : ""}`}
              onClick={() => setActiveTab("motifs")}
            >
              Motifs
            </button>
            <button
              className={`tab-btn ${activeTab === "metadata" ? "active" : ""}`}
              onClick={() => setActiveTab("metadata")}
            >
              Metadata
            </button>
            <button
              className={`tab-btn ${activeTab === "qa" ? "active" : ""}`}
              onClick={() => setActiveTab("qa")}
            >
              QA
            </button>
          </div>

          <div className="inspector-content">
            {activeTab === "characters" && (
              <CharacterSection 
                motif={motif} 
                setMotif={setMotif} 
                highlightedChars={highlightedChars}
                setHighlightedChars={setHighlightedChars}
              />
            )}

            {activeTab === "narrative" && (
              <NarrativeAndBiasSection
                narrativeStructure={narrativeStructure}
                setNarrativeStructure={setNarrativeStructure}
                crossValidation={crossValidation}
                setCrossValidation={setCrossValidation}
                motif={motif}
                currentSelection={currentSelection}
                onAddProppFn={onAddProppFn}
                highlightedRanges={highlightedRanges}
                setHighlightedRanges={setHighlightedRanges}
              />
            )}

            {activeTab === "propp" && (
              <DeepAnnotationSection
                proppFns={proppFns}
                setProppFns={setProppFns}
                proppNotes={proppNotes}
                setProppNotes={setProppNotes}
                currentSelection={currentSelection}
                onSync={handleSyncPropp}
                highlightedRanges={highlightedRanges}
                setHighlightedRanges={setHighlightedRanges}
                narrativeStructure={narrativeStructure}
              />
            )}

            {activeTab === "summaries" && (
              <SummariesSection
                paragraphSummaries={paragraphSummaries}
                setParagraphSummaries={setParagraphSummaries}
                sourceText={sourceText.text}
                setHighlightedRanges={setHighlightedRanges}
              />
            )}

            {activeTab === "motifs" && (
              <MotifSection motif={motif} setMotif={setMotif} />
            )}

            {activeTab === "metadata" && (
              <>
                <StoryMetadataSection
                  id={id}
                  culture={culture}
                  title={title}
                  onChangeId={setId}
                  onChangeCulture={setCulture}
                  onChangeTitle={setTitle}
                  sourceText={sourceText}
                  setSourceText={setSourceText}
                  annotationLevel={annotationLevel}
                  setAnnotationLevel={setAnnotationLevel}
                />
                <HighLevelMetaSection
                  meta={meta}
                  setMeta={setMeta}
                  deepMeta={deepMeta}
                  setDeepMeta={setDeepMeta}
                />
              </>
            )}

            {activeTab === "qa" && (
              <QASection
                qa={qa}
                setQa={setQa}
                persianSource={persianSource}
                setPersianSource={setPersianSource}
              />
            )}

            {showPreview && (
              <section className="card preview-card">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <h2>JSON Preview</h2>
                  <div className="inspector-tabs" style={{ border: "none", padding: 0 }}>
                    <button 
                      className={`tab-btn ${previewVersion === "v1" ? "active" : ""}`}
                      onClick={() => setPreviewVersion("v1")}
                    >
                      V1
                    </button>
                    <button 
                      className={`tab-btn ${previewVersion === "v2" ? "active" : ""}`}
                      onClick={() => setPreviewVersion("v2")}
                    >
                      V2
                    </button>
                  </div>
                </div>
                <pre className="json-preview">
                  {JSON.stringify(previewVersion === "v2" ? jsonV2 : jsonV1, null, 2)}
                </pre>
              </section>
            )}
          </div>
        </aside>
      </main>
    </div>
  );
}

function relPathToDatasetHint(path) {
  const normalized = path.replace(/^(\.\/|\/)+/, "");
  return normalized;
}

function StoryBrowserSection({
  storyFiles,
  selectedIndex,
  selectedStory,
  onFilesChange,
  onSelectStory,
  culture,
  onCultureChange
}) {
  return (
    <div className="story-browser">
      <div className="story-browser-header">
        <h2>Stories</h2>
        <label className="file-input-btn">
          Open Folder
          <input
            type="file"
            multiple
            webkitdirectory="true"
            directory="true"
            accept=".txt"
            onChange={onFilesChange}
          />
        </label>
      </div>

      <div style={{ padding: "0 0.5rem 0.5rem 0.5rem", borderBottom: "1px solid #e5e7eb" }}>
        <label style={{ fontSize: "0.8rem", display: "block", marginBottom: "0.25rem" }}>
          Default Culture
        </label>
        <select
          value={culture}
          onChange={(e) => onCultureChange(e.target.value)}
          style={{ width: "100%", padding: "0.25rem" }}
        >
          {["Chinese", "Persian", "Indian", "Japanese"].map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </div>

      <div className="story-list">
        {storyFiles.length === 0 && (
          <div className="empty-list-state">
            No stories loaded. Click "Open Folder" to load text files.
          </div>
        )}
        {storyFiles.map((s, idx) => (
          <button
            key={s.path || s.name + idx}
            type="button"
            className={`story-item ${idx === selectedIndex ? "active" : ""}`}
            onClick={() => onSelectStory(idx)}
          >
            <span className="story-item-name">{s.name}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

function StoryMetadataSection(props) {
  const {
    id,
    culture,
    title,
    onChangeId,
    onChangeCulture,
    onChangeTitle,
    sourceText,
    setSourceText,
    annotationLevel,
    setAnnotationLevel
  } = props;

  return (
    <section className="card">
      <h2>Story metadata</h2>
      <div className="grid-2">
        <label>
          Tale ID
          <input
            value={id}
            onChange={(e) => onChangeId(e.target.value)}
            placeholder="FA_006"
          />
        </label>
        <label>
          Culture
          <input
            value={culture}
            onChange={(e) => onChangeCulture(e.target.value)}
          />
        </label>
      </div>
      <label>
        Title
        <input
          value={title}
          onChange={(e) => onChangeTitle(e.target.value)}
          placeholder="Hassan Kachal (Bald Hassan)"
        />
      </label>

      <div className="grid-3">
        <label>
          Source language
          <input
            value={sourceText.language}
            onChange={(e) =>
              setSourceText({ ...sourceText, language: e.target.value })
            }
          />
        </label>
        <label>
          Source type
          <input
            value={sourceText.type}
            onChange={(e) =>
              setSourceText({ ...sourceText, type: e.target.value })
            }
            placeholder="summary / full_text"
          />
        </label>
        <label>
          Annotation level
          <select
            value={annotationLevel}
            onChange={(e) => setAnnotationLevel(e.target.value)}
          >
            <option value="Deep">Deep</option>
            <option value="Shallow">Shallow</option>
          </select>
        </label>
      </div>

      <label>
        Source text (summary or full text)
        <textarea
          rows={5}
          value={sourceText.text}
          onChange={(e) =>
            setSourceText({ ...sourceText, text: e.target.value })
          }
        />
      </label>

      <label>
        Reference URI
        <input
          value={sourceText.reference_uri}
          onChange={(e) =>
            setSourceText({ ...sourceText, reference_uri: e.target.value })
          }
          placeholder="file://datasets/iron/persian/persian/texts/FA_006_en.txt"
        />
      </label>
    </section>
  );
}

function HighLevelMetaSection({ meta, setMeta, deepMeta, setDeepMeta }) {
  const handleValuesChange = (e, which = "top") => {
    const values = multiSelectFromEvent(e);
    if (which === "top") {
      setMeta({ ...meta, key_values: values });
    } else {
      setDeepMeta({ ...deepMeta, key_values: values });
    }
  };

  return (
    <section className="card">
      <h2>High-level labels (ATU, values, ending)</h2>
      <div className="grid-3">
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

      <label>
        Key values (top-level)
        <select
          multiple
          value={meta.key_values}
          onChange={(e) => handleValuesChange(e, "top")}
        >
          {VALUE_TYPES.map((v) => (
            <option key={v} value={v}>
              {v}
            </option>
          ))}
        </select>
      </label>

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
            onChange={(e) => handleValuesChange(e, "deep")}
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

function CharacterSection({ motif, setMotif, highlightedChars, setHighlightedChars }) {
  const characters = Array.isArray(motif.character_archetypes)
    ? motif.character_archetypes
    : [];

  // Migration helper: if we encounter an old string array, treat as empty or migrate
  // For safety, let's assume we are starting fresh or user clears old data.
  // Actually, we can check if the first item is a string.
  const isLegacyFormat =
    characters.length > 0 && typeof characters[0] === "string";

  // If legacy, we can't easily edit it with this new UI, so let's reset it or map it.
  // Mapping approach: { name: "", alias: "", archetype: "TheStringValue" }
  const safeCharacters = isLegacyFormat
    ? characters.map((c) => ({ name: "", alias: "", archetype: c }))
    : characters;

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
        // Toggle Off
        delete next[name];
      } else {
        // Toggle On - pick a color not recently used or just cycle
        const usedColors = Object.values(next);
        // Find first color in HIGHLIGHT_COLORS not in usedColors
        let color = HIGHLIGHT_COLORS.find(c => !usedColors.includes(c));
        if (!color) {
          // Recycle colors if all used
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

  return (
    <section className="card">
      <h2>Characters</h2>
      <div className="section-header-row">
        <span>Story Characters</span>
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
      )})}

      <button type="button" className="ghost-btn" onClick={addCharacter} style={{ marginTop: "1rem" }}>
        + Add Character
      </button>

      <hr />

      <div className="grid-2">
        <label>
          Helper type
          <input
            value={motif.helper_type}
            onChange={(e) =>
              setMotif({ ...motif, helper_type: e.target.value })
            }
            placeholder="e.g. CAPTIVE_MAIDEN_AND_ANIMAL"
          />
        </label>
        <label>
          Obstacle thrower
          <input
            value={motif.obstacle_thrower}
            onChange={(e) =>
              setMotif({ ...motif, obstacle_thrower: e.target.value })
            }
            placeholder="Who throws the obstacles?"
          />
        </label>
      </div>
    </section>
  );
}

function MotifSection({ motif, setMotif }) {
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

function SummariesSection({ paragraphSummaries, setParagraphSummaries, sourceText, setHighlightedRanges }) {
  // Compute text paragraphs with character indices
  const textParagraphs = useMemo(() => {
    if (!sourceText) return [];
    const lines = sourceText.split('\n');
    const paras = [];
    let currentIndex = 0;

    lines.forEach((line) => {
      const len = line.length;
      if (line.trim()) {
        paras.push({
          text: line,
          start: currentIndex,
          end: currentIndex + len
        });
      }
      currentIndex += len + 1; // +1 for newline
    });
    return paras;
  }, [sourceText]);

  const { perParagraph = {}, combined = [], whole = "" } = paragraphSummaries;

  const updatePerParagraph = (index, value) => {
    setParagraphSummaries(prev => ({
      ...prev,
      perParagraph: { ...prev.perParagraph, [index]: value }
    }));
  };

  const updateCombined = (idx, field, value) => {
    setParagraphSummaries(prev => {
      const next = [...prev.combined];
      next[idx] = { ...next[idx], [field]: value };
      return { ...prev, combined: next };
    });
  };

  const addCombined = () => {
    setParagraphSummaries(prev => ({
      ...prev,
      combined: [...prev.combined, { start_para: 0, end_para: 0, text: "" }]
    }));
  };

  const removeCombined = (idx) => {
    setParagraphSummaries(prev => ({
      ...prev,
      combined: prev.combined.filter((_, i) => i !== idx)
    }));
  };

  const updateWhole = (value) => {
    setParagraphSummaries(prev => ({ ...prev, whole: value }));
  };

  const focusParagraph = (para) => {
    if (setHighlightedRanges && para) {
      setHighlightedRanges(prev => ({
        ...prev,
        "summary-focus": {
          start: para.start,
          end: para.end,
          color: "#86efac"
        }
      }));
    }
  };

  const focusCombined = (item) => {
    let startChar = Infinity;
    let endChar = -Infinity;
    const pStart = Math.min(item.start_para, item.end_para);
    const pEnd = Math.max(item.start_para, item.end_para);

    for (let i = pStart; i <= pEnd; i++) {
      const p = textParagraphs[i];
      if (p) {
        startChar = Math.min(startChar, p.start);
        endChar = Math.max(endChar, p.end);
      }
    }

    if (startChar !== Infinity && setHighlightedRanges) {
      setHighlightedRanges(prev => ({
        ...prev,
        "summary-focus": {
          start: startChar,
          end: endChar,
          color: "#86efac"
        }
      }));
    }
  };

  return (
    <section className="card">
      <h2>Summaries</h2>

      {/* Section 1: Per-Paragraph Summaries */}
      <div style={{ marginBottom: "1.5rem" }}>
        <div className="section-header-row">
          <span style={{ fontWeight: "bold" }}>Per-Paragraph Summaries</span>
          <span style={{ fontSize: "0.75rem", color: "#6b7280" }}>({textParagraphs.length} paragraphs)</span>
        </div>

        {textParagraphs.length === 0 && (
          <p className="hint">No text loaded.</p>
        )}

        {textParagraphs.map((para, idx) => {
          const preview = para.text.length > 50 ? para.text.substring(0, 50) + "..." : para.text;
          const summaryText = perParagraph[idx] || "";

          return (
            <div key={idx} style={{ marginBottom: "0.75rem", border: "1px solid #e5e7eb", padding: "0.5rem", borderRadius: "4px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.25rem" }}>
                <span style={{ fontWeight: "bold", fontSize: "0.8rem" }}>
                  Paragraph {idx + 1}
                  <span style={{ fontWeight: "normal", color: "#6b7280", marginLeft: "0.5rem" }}>
                    ({para.start}-{para.end})
                  </span>
                </span>
                <button
                  type="button"
                  className="ghost-btn"
                  style={{ padding: "2px 6px", fontSize: "0.7rem" }}
                  onClick={() => focusParagraph(para)}
                >
                  Highlight
                </button>
              </div>
              <div style={{ fontSize: "0.7rem", color: "#666", marginBottom: "0.25rem", fontStyle: "italic", background: "#f9fafb", padding: "0.25rem", borderRadius: "2px" }}>
                "{preview}"
              </div>
              <textarea
                rows={2}
                value={summaryText}
                onChange={(e) => updatePerParagraph(idx, e.target.value)}
                placeholder={`Summary for paragraph ${idx + 1}...`}
                style={{ width: "100%", fontSize: "0.85rem" }}
                onFocus={() => focusParagraph(para)}
              />
            </div>
          );
        })}
      </div>

      <hr />

      {/* Section 2: Combined Paragraph Summaries */}
      <div style={{ marginBottom: "1.5rem" }}>
        <div className="section-header-row">
          <span style={{ fontWeight: "bold" }}>Combined Paragraph Summaries</span>
        </div>

        {combined.length === 0 && (
          <p className="hint">No combined summaries. Use the button below to add one.</p>
        )}

        {combined.map((item, idx) => {
          const pStart = Math.min(item.start_para, item.end_para);
          const pEnd = Math.max(item.start_para, item.end_para);
          const relevantParas = textParagraphs.slice(pStart, pEnd + 1);
          const fullText = relevantParas.map(p => p.text).join(" ");
          const preview = fullText.length > 60 ? fullText.substring(0, 60) + "..." : fullText;

          // Calculate char range for display
          let charStart = relevantParas[0]?.start ?? 0;
          let charEnd = relevantParas[relevantParas.length - 1]?.end ?? 0;

          return (
            <div key={idx} style={{ marginBottom: "0.75rem", border: "1px solid #d1d5db", padding: "0.5rem", borderRadius: "4px", background: "#fefce8" }}>
              <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", marginBottom: "0.5rem" }}>
                <span style={{ fontWeight: "bold", fontSize: "0.8rem" }}>Range:</span>
                <label style={{ fontSize: "0.8rem" }}>
                  Start:
                  <input
                    type="number"
                    min="0"
                    max={textParagraphs.length - 1}
                    value={item.start_para}
                    onChange={(e) => updateCombined(idx, "start_para", parseInt(e.target.value) || 0)}
                    style={{ width: "50px", marginLeft: "0.25rem" }}
                  />
                </label>
                <label style={{ fontSize: "0.8rem" }}>
                  End:
                  <input
                    type="number"
                    min="0"
                    max={textParagraphs.length - 1}
                    value={item.end_para}
                    onChange={(e) => updateCombined(idx, "end_para", parseInt(e.target.value) || 0)}
                    style={{ width: "50px", marginLeft: "0.25rem" }}
                  />
                </label>
                <span style={{ fontSize: "0.75rem", color: "#6b7280" }}>
                  (chars: {charStart}-{charEnd})
                </span>
                <button
                  type="button"
                  className="ghost-btn"
                  style={{ padding: "2px 6px", fontSize: "0.7rem", marginLeft: "auto" }}
                  onClick={() => focusCombined(item)}
                >
                  Highlight
                </button>
                <button
                  type="button"
                  className="ghost-btn"
                  style={{ color: "#ef4444", borderColor: "#ef4444", padding: "2px 6px", fontSize: "0.7rem" }}
                  onClick={() => removeCombined(idx)}
                >
                  X
                </button>
              </div>
              <div style={{ fontSize: "0.7rem", color: "#666", marginBottom: "0.25rem", fontStyle: "italic", background: "#fff", padding: "0.25rem", borderRadius: "2px" }}>
                Preview: "{preview || "Invalid Range"}"
              </div>
              <textarea
                rows={2}
                value={item.text}
                onChange={(e) => updateCombined(idx, "text", e.target.value)}
                placeholder="Combined summary..."
                style={{ width: "100%", fontSize: "0.85rem" }}
                onFocus={() => focusCombined(item)}
              />
            </div>
          );
        })}

        <button type="button" className="ghost-btn" onClick={addCombined}>
          + Add Combined Summary
        </button>
      </div>

      <hr />

      {/* Section 3: Whole Story Summary */}
      <div>
        <div className="section-header-row">
          <span style={{ fontWeight: "bold" }}>Whole Story Summary</span>
        </div>
        <textarea
          rows={4}
          value={whole}
          onChange={(e) => updateWhole(e.target.value)}
          placeholder="Write a summary of the entire story..."
          style={{ width: "100%", fontSize: "0.9rem" }}
        />
      </div>
    </section>
  );
}

function DeepAnnotationSection({
  proppFns,
  setProppFns,
  proppNotes,
  setProppNotes,
  currentSelection,
  onSync,
  highlightedRanges,
  setHighlightedRanges,
  narrativeStructure
}) {
  const validNarrativeIds = useMemo(() => {
    return new Set((narrativeStructure || []).map(n => n.id).filter(Boolean));
  }, [narrativeStructure]);

  const handleProppChange = (idx, field, value) => {
    const next = proppFns.map((item, i) =>
      i === idx
        ? {
            ...item,
            [field]:
              field === "textSpan"
                ? { ...item[field], ...value }
                : value
          }
        : item
    );
    setProppFns(next);
  };

  const captureSelection = (idx) => {
    if (!currentSelection) return;
    const next = proppFns.map((item, i) =>
      i === idx
        ? {
            ...item,
            textSpan: currentSelection,
            evidence: currentSelection.text // Auto-fill evidence too? Optional but helpful
          }
        : item
    );
    setProppFns(next);
  };

  const addPropp = () => {
    setProppFns([...proppFns, emptyProppFn()]);
  };

  const removePropp = (index) => {
    const next = proppFns.filter((_, i) => i !== index);
    setProppFns(next);
  };

  const toggleHighlight = (idx, span) => {
    if (!setHighlightedRanges || !span) return;
    const key = `propp-${idx}`;

    setHighlightedRanges(prev => {
      const next = { ...prev };
      if (next[key]) {
        delete next[key];
      } else {
        next[key] = {
          start: span.start,
          end: span.end,
          color: "#c084fc" // Purple for propp
        };
      }
      return next;
    });
  };

  const isHighlighted = (idx) => {
    return highlightedRanges && !!highlightedRanges[`propp-${idx}`];
  };

  return (
    <section className="card">
      <h2>Propp Functions</h2>

      <div className="section-header-row">
        <span>Propp functions</span>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <button type="button" className="ghost-btn" onClick={onSync} title="Create missing Propp functions from Narrative events">
            Sync from Narrative
          </button>
        </div>
      </div>

      {proppFns.map((fnObj, idx) => {
        const isLinked = fnObj.narrative_event_id && validNarrativeIds.has(fnObj.narrative_event_id);
        const isOrphan = fnObj.narrative_event_id && !validNarrativeIds.has(fnObj.narrative_event_id);

        return (
          <div key={idx} className="propp-row" style={isOrphan ? { borderLeft: "4px solid #ef4444", paddingLeft: "8px" } : {}}>
            {isOrphan && (
              <div style={{ color: "#ef4444", fontSize: "0.8rem", marginBottom: "0.5rem", fontWeight: "bold" }}>
                ⚠️ Unlinked from Narrative
              </div>
            )}
            <div className="grid-2">
              <div>
                <label>Function</label>
              <select
                value={fnObj.fn}
                onChange={(e) => handleProppChange(idx, "fn", e.target.value)}
              >
                <option value="">–</option>
                {PROPP_FUNCTIONS.map((fn) => (
                  <option key={fn} value={fn}>
                    {fn}
                  </option>
                ))}
                </select>
              </div>
              <div>
                <label>Text Selection</label>
                <div style={{ display: "flex", gap: "0.5rem" }}>
                <input
                  type="number"
                  value={fnObj.textSpan?.start || 0}
                  readOnly
                    style={{ background: "#e5e7eb", width: "60px" }}
                />
                  <span style={{ alignSelf: "center" }}>-</span>
                <input
                  type="number"
                  value={fnObj.textSpan?.end || 0}
                  readOnly
                    style={{ background: "#e5e7eb", width: "60px" }}
                  />
                  <button
                    type="button"
                    className="primary-btn"
                    style={{ padding: "0.5rem", fontSize: "0.75rem", height: "34px", whiteSpace: "nowrap" }}
                    onClick={() => captureSelection(idx)}
                    disabled={!currentSelection}
                  >
                    Capture
                  </button>
                  <button
                    type="button"
                    className={`ghost-btn ${isHighlighted(idx) ? "active-highlight" : ""}`}
                    style={{
                      padding: "0.5rem",
                      fontSize: "0.75rem",
                      height: "34px",
                      background: isHighlighted(idx) ? "#c084fc" : undefined,
                      color: isHighlighted(idx) ? "#fff" : undefined,
                      fontWeight: isHighlighted(idx) ? "bold" : undefined,
                      whiteSpace: "nowrap"
                    }}
                    onClick={() => toggleHighlight(idx, fnObj.textSpan)}
                    disabled={!fnObj.textSpan}
                  >
                    {isHighlighted(idx) ? "Hide" : "Highlight"}
                  </button>
                </div>
              </div>
            </div>

          <label>
            Evidence
            <textarea
              rows={2}
              value={fnObj.evidence}
              onChange={(e) =>
                handleProppChange(idx, "evidence", e.target.value)
              }
            />
          </label>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
              {!isLinked && (
                <button
                  type="button"
                  className="ghost-btn"
                  style={{ color: "#ef4444", borderColor: "#ef4444" }}
                  onClick={() => removePropp(idx)}
                >
                  {isOrphan ? "Delete Unlinked Propp" : "Remove Function"}
                </button>
              )}
            </div>
          </div>
        )
      })}

      <button type="button" className="ghost-btn" onClick={addPropp} style={{ marginTop: "1rem" }}>
        + Add function
      </button>

      <label>
        Propp notes
        <textarea
          rows={2}
          value={proppNotes}
          onChange={(e) => setProppNotes(e.target.value)}
        />
      </label>
    </section>
  );
}

function NarrativeAndBiasSection({
  narrativeStructure,
  setNarrativeStructure,
  crossValidation,
  setCrossValidation,
  motif,
  currentSelection,
  onAddProppFn,
  highlightedRanges,
  setHighlightedRanges
}) {
  // 1. Prepare Character Options from motif state
  // We prefer names, fallback to archetypes if name is missing
  const charactersList = Array.isArray(motif.character_archetypes)
    ? motif.character_archetypes
    : [];
  
  // Flatten to a list of options: { label: "Aladdin (Hero)", value: "Aladdin" }
  const characterOptions = charactersList
    .map((c) => {
      if (typeof c === "string") return { label: c, value: c }; // Legacy string
      const name = c.name || "Unnamed";
      const role = c.archetype || "Unknown";
      return { label: `${name} (${role})`, value: name };
    })
    .filter((o) => o.value && o.value !== "Unnamed");

  // 2. Prepare Narrative Items (Migration from strings if needed)
  const items = narrativeStructure.map((item) => {
    if (typeof item === "string") {
      return       {
        id: generateUUID(),
        event_type: "OTHER",
        description: item,
        agents: [],
        targets: [],
        text_span: null,
        target_type: "",
        object_type: "",
        instrument: ""
      };
    }
    // Ensure ID exists for existing object items (migration for V2 files without IDs)
    if (!item.id) {
      // Note: In a pure render function, generating random IDs is bad (unstable keys).
      // But since we use index as key in map below, it might be okay for display, 
      // BUT edits will fail if we don't persist this ID back to state.
      // Ideally `mapV2ToState` handles this. 
      // We'll trust `item.id` exists or fallback to a stable-ish ID if possible, or just random.
      // Actually, we should just return it as is, and rely on `mapV2ToState` to have populated it.
      // If it's missing, let's just generate one, but this might cause re-render loop if we triggered an update.
      // Let's assume mapV2ToState did its job.
      return { ...item, id: generateUUID() };
    }
    return item;
  });

  const updateItem = (index, field, value) => {
    const next = [...items];
    next[index] = { ...next[index], [field]: value };
    setNarrativeStructure(next);

    // Auto-generate Propp if specific fields changed
    if (onAddProppFn && field === "event_type") {
      // We pass the updated item, but we need to merge the new value first
      const updatedItem = { ...next[index], [field]: value };
      onAddProppFn(updatedItem);
    }
  };

  const addItem = () => {
    setNarrativeStructure([
      ...items,
      {
        id: generateUUID(),
        event_type: "",
        description: "",
        agents: [],
        targets: [],
        text_span: null,
        target_type: "",
        object_type: "",
        instrument: ""
      }
    ]);
  };

  const removeItem = (index) => {
    const next = items.filter((_, i) => i !== index);
    setNarrativeStructure(next);
  };

  const captureSelection = (index) => {
    if (!currentSelection) return;
    updateItem(index, "text_span", currentSelection);
    // Optional: auto-fill description if empty?
    // updateItem(index, "description", currentSelection.text.substring(0, 50) + "...");
  };

  const toggleHighlight = (idx, span) => {
    if (!setHighlightedRanges || !span) return;
    const key = `narrative-${idx}`;

    setHighlightedRanges(prev => {
      const next = { ...prev };
      if (next[key]) {
        delete next[key];
      } else {
        next[key] = {
          start: span.start,
          end: span.end,
          color: "#fca5a5" // Light red/orange for narrative events
        };
      }
      return next;
    });
  };

  const isHighlighted = (idx) => {
    return highlightedRanges && !!highlightedRanges[`narrative-${idx}`];
  };

  // Helper for multi-select (Agents/Targets)
  const handleMultiCharChange = (index, field, newValue) => {
    // newValue is an array of objects { label, value } from react-select
    const values = newValue ? newValue.map(o => o.value) : [];
    updateItem(index, field, values);
  };

  const handleBiasChange = (field, value) => {
    setCrossValidation({
      ...crossValidation,
      bias_reflection: {
        ...crossValidation.bias_reflection,
        [field]: value
      }
    });
  };

  const handleAmbiguousMotifsChange = (idx, value) => {
    const current = crossValidation.bias_reflection.ambiguous_motifs || [];
    const next = [...current];
    next[idx] = value;
    setCrossValidation({
      ...crossValidation,
      bias_reflection: {
        ...crossValidation.bias_reflection,
        ambiguous_motifs: next
      }
    });
  };

  const addAmbiguousMotif = () => {
    const current = crossValidation.bias_reflection.ambiguous_motifs || [];
    setCrossValidation({
      ...crossValidation,
      bias_reflection: {
        ...crossValidation.bias_reflection,
        ambiguous_motifs: [...current, ""]
      }
    });
  };

  return (
    <section className="card">
      <h2>Narrative Events</h2>
      <div className="section-header-row">
        <span>Story Sequence</span>
      </div>

      {items.map((item, idx) => (
        <div key={idx} className="propp-row">
          <div className="grid-2">
            <div>
              <label>Event Type (Propp)</label>
              <select
                value={item.event_type}
                onChange={(e) => updateItem(idx, "event_type", e.target.value)}
              >
                <option value="">– Select Event –</option>
                {PROPP_FUNCTIONS.map((fn) => (
                  <option key={fn} value={fn}>
                    {fn}
                  </option>
                ))}
                <option value="OTHER">OTHER</option>
              </select>
            </div>
            <div>
              <label>Text Selection</label>
              <div style={{ display: "flex", gap: "0.5rem" }}>
                <input
                  value={
                    item.text_span
                      ? `${item.text_span.start}-${item.text_span.end}`
                      : "None"
                  }
                  readOnly
                  placeholder="No selection"
                  style={{ background: "#f3f4f6", marginBottom: 0, flex: 1 }}
                />
                <button
                  type="button"
                  className="primary-btn"
                  style={{ padding: "0.5rem", fontSize: "0.75rem", height: "34px", whiteSpace: "nowrap" }}
                  onClick={() => captureSelection(idx)}
                  disabled={!currentSelection}
                >
                  Capture
                </button>
                <button
                  type="button"
                  className={`ghost-btn ${isHighlighted(idx) ? "active-highlight" : ""}`}
                  style={{
                    padding: "0.5rem",
                    fontSize: "0.75rem",
                    height: "34px",
                    background: isHighlighted(idx) ? "#fca5a5" : undefined,
                    color: isHighlighted(idx) ? "#000" : undefined,
                    fontWeight: isHighlighted(idx) ? "bold" : undefined,
                    whiteSpace: "nowrap"
                  }}
                  onClick={() => toggleHighlight(idx, item.text_span)}
                  disabled={!item.text_span}
                >
                  {isHighlighted(idx) ? "Hide" : "Highlight"}
                </button>
              </div>
            </div>
          </div>

          <label>
            Description / Detail
            <textarea
              rows={2}
              value={item.description}
              onChange={(e) => updateItem(idx, "description", e.target.value)}
              placeholder="Describe the specific event..."
            />
          </label>

          <div className="grid-2">
            <label>
              Agents (Doer)
              <CreatableSelect
                isMulti
                options={characterOptions}
                value={(item.agents || []).map(agentName => {
                  const found = characterOptions.find(opt => opt.value === agentName);
                  return found || { label: agentName, value: agentName };
                })}
                onChange={(newValue) => handleMultiCharChange(idx, "agents", newValue)}
                placeholder="Select or create agents..."
                styles={customStyles}
              />
            </label>
            <label>
              Targets (Receiver)
              {item.target_type === "object" ? (
                <input
                  value={item.targets && item.targets.length > 0 ? item.targets[0] : ""}
                  onChange={(e) => updateItem(idx, "targets", [e.target.value])}
                  placeholder="Enter object target name..."
                  style={{ marginTop: '4px', width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
                />
              ) : (
                <CreatableSelect
                  isMulti
                  options={characterOptions}
                    value={(item.targets || []).map(targetName => {
                      const found = characterOptions.find(opt => opt.value === targetName);
                      return found || { label: targetName, value: targetName };
                    })}
                  onChange={(newValue) => handleMultiCharChange(idx, "targets", newValue)}
                  placeholder="Select or create targets..."
                  styles={customStyles}
                />
              )}
            </label>
          </div>

          <div className="grid-3">
            <label>
              Target Type
              <select
                value={item.target_type || ""}
                onChange={(e) => updateItem(idx, "target_type", e.target.value)}
              >
                <option value="">– Select –</option>
                {TARGET_CATEGORIES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </label>
            {item.target_type === "object" && (
              <label>
                Object Type
                <select
                  value={item.object_type || ""}
                  onChange={(e) => updateItem(idx, "object_type", e.target.value)}
                >
                  <option value="">– Select –</option>
                  {OBJECT_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </label>
            )}
            <label>
              Instrument
              <input
                value={item.instrument || ""}
                onChange={(e) => updateItem(idx, "instrument", e.target.value)}
                placeholder="Instrument used..."
              />
            </label>
          </div>
          
          <button
            type="button"
            className="ghost-btn"
            style={{ color: "#ef4444", borderColor: "#ef4444", marginTop: "0.5rem" }}
            onClick={() => removeItem(idx)}
          >
            Remove Event
          </button>
        </div>
      ))}

      <button type="button" className="ghost-btn" onClick={addItem} style={{ marginTop: "1rem" }}>
        + Add Event
      </button>

      <hr />

      <h3>Bias reflection</h3>
      <label>
        Cultural reading
        <textarea
          rows={2}
          value={crossValidation.bias_reflection.cultural_reading}
          onChange={(e) => handleBiasChange("cultural_reading", e.target.value)}
        />
      </label>
      <label>
        Gender norms
        <textarea
          rows={2}
          value={crossValidation.bias_reflection.gender_norms}
          onChange={(e) => handleBiasChange("gender_norms", e.target.value)}
        />
      </label>
      <label>
        Hero/villain mapping
        <textarea
          rows={2}
          value={crossValidation.bias_reflection.hero_villain_mapping}
          onChange={(e) =>
            handleBiasChange("hero_villain_mapping", e.target.value)
          }
        />
      </label>

      <div className="section-header-row">
        <span>Ambiguous motifs</span>
        <button
          type="button"
          className="ghost-btn"
          onClick={addAmbiguousMotif}
        >
          + Add motif
        </button>
      </div>
      {(crossValidation.bias_reflection.ambiguous_motifs || []).map(
        (m, idx) => (
          <input
            key={idx}
            value={m}
            onChange={(e) => handleAmbiguousMotifsChange(idx, e.target.value)}
          />
        )
      )}
    </section>
  );
}

function QASection({ qa, setQa, persianSource, setPersianSource }) {
  return (
    <section className="card">
      <h2>QA & Persian source</h2>
      <div className="grid-3">
        <label>
          Annotator
          <input
            value={qa.annotator}
            onChange={(e) => setQa({ ...qa, annotator: e.target.value })}
          />
        </label>
        <label>
          Date annotated
          <input
            type="date"
            value={qa.date_annotated}
            onChange={(e) =>
              setQa({ ...qa, date_annotated: e.target.value })
            }
          />
        </label>
        <label>
          Confidence (0–1)
          <input
            type="number"
            step="0.01"
            min="0"
            max="1"
            value={qa.confidence}
            onChange={(e) =>
              setQa({ ...qa, confidence: Number(e.target.value) })
            }
          />
        </label>
      </div>

      <label>
        QA notes
        <textarea
          rows={2}
          value={qa.notes}
          onChange={(e) => setQa({ ...qa, notes: e.target.value })}
        />
      </label>

      <hr />

      <h3>Persian source text</h3>
      <div className="grid-3">
        <label>
          Language
          <input
            value={persianSource.language}
            onChange={(e) =>
              setPersianSource({
                ...persianSource,
                language: e.target.value
              })
            }
          />
        </label>
        <label>
          Type
          <input
            value={persianSource.type}
            onChange={(e) =>
              setPersianSource({ ...persianSource, type: e.target.value })
            }
            placeholder="excerpt / full_text"
          />
        </label>
        <label>
          Reference URI
          <input
            value={persianSource.reference_uri}
            onChange={(e) =>
              setPersianSource({
                ...persianSource,
                reference_uri: e.target.value
              })
            }
          />
        </label>
      </div>

      <label>
        Persian text
        <textarea
          rows={3}
          value={persianSource.text}
          onChange={(e) =>
            setPersianSource({ ...persianSource, text: e.target.value })
          }
        />
      </label>
    </section>
  );
}


