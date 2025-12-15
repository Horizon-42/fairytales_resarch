import React, { useMemo, useState } from "react";
import {
  ATU_TYPES,
  CHARACTER_ARCHETYPES,
  VALUE_TYPES,
  ENDING_TYPES,
  PROPP_FUNCTIONS
} from "./constants.js";

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

const emptyProppFn = () => ({
  fn: "",
  spanType: "paragraph", // "paragraph" or "text"
  span: { start: 0, end: 0 }, // For paragraphs
  textSpan: { start: 0, end: 0, text: "" }, // For raw text index
  evidence: ""
});

export default function App() {
  const [storyFiles, setStoryFiles] = useState([]);
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

  const jsonPreview = useMemo(
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
      narrative_structure: narrativeStructure.filter((n) => n.trim()),
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

  const handleDownload = () => {
    const filename = `${id || "annotation"}.json`;
    downloadJson(filename, jsonPreview);
  };

  const handleStoryFilesChange = async (event) => {
    const files = Array.from(event.target.files || []).filter((f) =>
      f.name.toLowerCase().endsWith(".txt")
    );
    const withContent = await Promise.all(
      files.map(async (file) => {
        const text = await file.text();
        const relPath = file.webkitRelativePath || file.name;
        return { file, name: file.name, path: relPath, text };
      })
    );
    // Sort stories alphabetically by name
    withContent.sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true, sensitivity: 'base' }));
    
    setStoryFiles(withContent);
    if (withContent.length > 0) {
      const first = withContent[0];
      setSelectedStoryIndex(0);
      // Try to derive ID from filename like FA_006_*.txt
      const idGuess = first.name.split(/[_.]/)[0] || "FA_XXX";
      setId(idGuess);
      setSourceText((prev) => ({
        ...prev,
        text: first.text,
        reference_uri: `file://${relPathToDatasetHint(first.path)}`
      }));
    }
  };

  const handleSelectStory = (index) => {
    setSelectedStoryIndex(index);
    const story = storyFiles[index];
    if (story) {
      const idGuess = story.name.split(/[_.]/)[0] || id;
      setId(idGuess);
      setSourceText((prev) => ({
        ...prev,
        text: story.text,
        reference_uri: `file://${relPathToDatasetHint(story.path)}`
      }));
    }
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
          <button className="primary-btn" onClick={handleDownload}>
            Download JSON
          </button>
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
                  <pre id="story-content-pre">{storyFiles[selectedStoryIndex].text}</pre>
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
              className={`tab-btn ${activeTab === "motifs" ? "active" : ""}`}
              onClick={() => setActiveTab("motifs")}
            >
              Motifs
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
              <CharacterSection motif={motif} setMotif={setMotif} />
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

            {activeTab === "motifs" && (
              <MotifSection motif={motif} setMotif={setMotif} />
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
                <h2>JSON Preview</h2>
                <pre className="json-preview">
                  {JSON.stringify(jsonPreview, null, 2)}
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
  onSelectStory
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

function CharacterSection({ motif, setMotif }) {
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

      {safeCharacters.map((char, idx) => (
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
                placeholder="e.g. Street Rat"
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
          <button
            type="button"
            className="ghost-btn"
            style={{ color: "#ef4444", borderColor: "#ef4444", marginTop: "0.25rem" }}
            onClick={() => removeCharacter(idx)}
          >
            Remove
          </button>
        </div>
      ))}

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


