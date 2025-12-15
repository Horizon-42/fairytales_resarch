import React, { useMemo, useState, useEffect, useRef } from "react";
import {
  ATU_TYPES,
  CHARACTER_ARCHETYPES,
  VALUE_TYPES,
  ENDING_TYPES,
  PROPP_FUNCTIONS
} from "./constants.js";
import { organizeFiles, mapV1ToState, mapV2ToState } from "./utils/fileHandler.js";

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
  fn: "",
  spanType: "paragraph", // "paragraph" or "text"
  span: { start: 0, end: 0 }, // For paragraphs
  textSpan: { start: 0, end: 0, text: "" }, // For raw text index
  evidence: ""
});

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

  const [paragraphSummaries, setParagraphSummaries] = useState([""]);
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
          paragraph_summaries: paragraphSummaries.filter((p) => p.trim()),
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
        paragraph_summaries: paragraphSummaries.filter((p) => p.trim()),
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
    
    if (loaded.paragraphSummaries) setParagraphSummaries(loaded.paragraphSummaries);
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
    setParagraphSummaries([""]);
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
        const text = await t.file.text();
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
  const [lastAutoSave, setLastAutoSave] = useState(null);

  const onAddProppFn = (newEvent) => {
    // Only add if event_type is not empty and not "OTHER"
    if (!newEvent.event_type || newEvent.event_type === "OTHER") return;

    setProppFns((prev) => [
      ...prev,
      {
        fn: newEvent.event_type,
        spanType: "text",
        span: { start: 0, end: 0 },
        textSpan: newEvent.text_span || { start: 0, end: 0, text: "" },
        evidence: newEvent.description || ""
      }
    ]);
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

                      if (!allTerms.length) return text;
                      
                      // Sort by length descending to match longest terms first
                      allTerms.sort((a, b) => b.length - a.length);
                      
                      // Escape regex
                      const escapedTerms = allTerms.map(t => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
                      const regex = new RegExp(`(${escapedTerms.join("|")})`, "gi");
                      
                      const parts = text.split(regex);
                      
                      return parts.map((part, i) => {
                        const lower = part.toLowerCase();
                        // Check exact match (case-insensitive) in our map
                        // Since split captures the delimiter, 'part' IS one of the terms if it matched.
                        // However, we need to find WHICH color.
                        // We look up in termMap.
                        const color = termMap[lower];
                        
                        if (color) {
                          return (
                            <mark 
                              key={i} 
                              className="highlighted-text" 
                              style={{ backgroundColor: color, color: "#000", borderRadius: "2px", padding: "0 2px" }}
                            >
                              {part}
                            </mark>
                          );
                        }
                        return part;
                      });
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
              />
            )}

            {activeTab === "propp" && (
              <DeepAnnotationSection
                proppFns={proppFns}
                setProppFns={setProppFns}
                proppNotes={proppNotes}
                setProppNotes={setProppNotes}
                currentSelection={currentSelection}
              />
            )}

            {activeTab === "summaries" && (
              <SummariesSection
                paragraphSummaries={paragraphSummaries}
                setParagraphSummaries={setParagraphSummaries}
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
        <button type="button" className="ghost-btn" onClick={addCharacter}>
          + Add Character
        </button>
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

function SummariesSection({ paragraphSummaries, setParagraphSummaries }) {
  const handleParagraphChange = (index, value) => {
    const next = [...paragraphSummaries];
    next[index] = value;
    setParagraphSummaries(next);
  };

  const addParagraph = () => {
    setParagraphSummaries([...paragraphSummaries, ""]);
  };

  return (
    <section className="card">
      <h2>Paragraph Summaries</h2>
      <div className="section-header-row">
        <span>Summaries</span>
        <button type="button" className="ghost-btn" onClick={addParagraph}>
          + Add paragraph
        </button>
      </div>
      {paragraphSummaries.map((p, idx) => (
        <label key={idx}>
          Paragraph {idx}
          <textarea
            rows={2}
            value={p}
            onChange={(e) => handleParagraphChange(idx, e.target.value)}
          />
        </label>
      ))}
    </section>
  );
}

function DeepAnnotationSection({
  proppFns,
  setProppFns,
  proppNotes,
  setProppNotes,
  currentSelection
}) {
  const handleProppChange = (idx, field, value) => {
    const next = proppFns.map((item, i) =>
      i === idx
        ? {
            ...item,
            [field]:
              field === "span" || field === "textSpan"
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

  return (
    <section className="card">
      <h2>Propp Functions</h2>

      <div className="section-header-row">
        <span>Propp functions</span>
        <button type="button" className="ghost-btn" onClick={addPropp}>
          + Add function
        </button>
      </div>

      {proppFns.map((fnObj, idx) => (
        <div key={idx} className="propp-row">
          <div className="grid-2" style={{ marginBottom: "0.5rem" }}>
            <label>
              Function
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
            </label>
            <label>
              Span Type
              <select
                value={fnObj.spanType || "paragraph"}
                onChange={(e) =>
                  handleProppChange(idx, "spanType", e.target.value)
                }
              >
                <option value="paragraph">Paragraph Index</option>
                <option value="text">Text Selection</option>
              </select>
            </label>
          </div>

          {(fnObj.spanType === "text") ? (
            <div className="grid-3" style={{ alignItems: "end" }}>
              <label>
                Start Index
                <input
                  type="number"
                  value={fnObj.textSpan?.start || 0}
                  readOnly
                  style={{ background: "#e5e7eb" }}
                />
              </label>
              <label>
                End Index
                <input
                  type="number"
                  value={fnObj.textSpan?.end || 0}
                  readOnly
                  style={{ background: "#e5e7eb" }}
                />
              </label>
              <button
                type="button"
                className="primary-btn"
                style={{ marginBottom: "0.75rem", fontSize: "0.75rem", padding: "0.5rem" }}
                onClick={() => captureSelection(idx)}
                disabled={!currentSelection}
              >
                Capture Selection
              </button>
            </div>
          ) : (
            <div className="grid-2">
              <label>
                Start Para
                <input
                  type="number"
                  value={fnObj.span?.start || 0}
                  onChange={(e) =>
                    handleProppChange(idx, "span", {
                      start: Number(e.target.value)
                    })
                  }
                />
              </label>
              <label>
                End Para
                <input
                  type="number"
                  value={fnObj.span?.end || 0}
                  onChange={(e) =>
                    handleProppChange(idx, "span", {
                      end: Number(e.target.value)
                    })
                  }
                />
              </label>
            </div>
          )}

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
        </div>
      ))}

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
  onAddProppFn
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
      return {
        event_type: "OTHER",
        description: item,
        agents: [],
        targets: [],
        text_span: null
      };
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
        event_type: "",
        description: "",
        agents: [],
        targets: [],
        text_span: null
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

  // Helper for multi-select (Agents/Targets)
  const handleMultiCharChange = (index, field, e) => {
    const values = Array.from(e.target.selectedOptions).map((o) => o.value);
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
        <button type="button" className="ghost-btn" onClick={addItem}>
          + Add Event
        </button>
      </div>

      {items.map((item, idx) => (
        <div key={idx} className="propp-row">
          <div className="grid-2">
            <label>
              Event Type (Propp)
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
            </label>
            <div style={{ display: "flex", alignItems: "flex-end", gap: "0.5rem" }}>
              <label style={{ flex: 1 }}>
                Text Selection
                <input
                  value={
                    item.text_span
                      ? `${item.text_span.start}-${item.text_span.end}`
                      : "None"
                  }
                  readOnly
                  placeholder="No selection"
                  style={{ background: "#f3f4f6", marginBottom: 0 }}
                />
              </label>
              <button
                type="button"
                className="primary-btn"
                style={{ padding: "0.5rem", fontSize: "0.75rem", height: "34px" }}
                onClick={() => captureSelection(idx)}
                disabled={!currentSelection}
              >
                Capture
              </button>
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
              <select
                multiple
                value={item.agents || []}
                onChange={(e) => handleMultiCharChange(idx, "agents", e)}
                style={{ height: "80px" }}
              >
                {characterOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Targets (Receiver)
              <select
                multiple
                value={item.targets || []}
                onChange={(e) => handleMultiCharChange(idx, "targets", e)}
                style={{ height: "80px" }}
              >
                {characterOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
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


