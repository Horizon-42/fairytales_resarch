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
  span: { start: 0, end: 0 },
  evidence: ""
});

export default function App() {
  const [storyFiles, setStoryFiles] = useState([]);
  const [selectedStoryIndex, setSelectedStoryIndex] = useState(-1);

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

  const [activeTab, setActiveTab] = useState("metadata");

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
                <div className="story-text-display">
                  <pre>{storyFiles[selectedStoryIndex].text}</pre>
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
              className={`tab-btn ${activeTab === "metadata" ? "active" : ""}`}
              onClick={() => setActiveTab("metadata")}
            >
              Metadata
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
              className={`tab-btn ${activeTab === "narrative" ? "active" : ""}`}
              onClick={() => setActiveTab("narrative")}
            >
              Narrative
            </button>
            <button
              className={`tab-btn ${activeTab === "qa" ? "active" : ""}`}
              onClick={() => setActiveTab("qa")}
            >
              QA
            </button>
          </div>

          <div className="inspector-content">
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

            {activeTab === "motifs" && (
              <MotifSection motif={motif} setMotif={setMotif} />
            )}

            {activeTab === "propp" && (
              <DeepAnnotationSection
                paragraphSummaries={paragraphSummaries}
                setParagraphSummaries={setParagraphSummaries}
                proppFns={proppFns}
                setProppFns={setProppFns}
                proppNotes={proppNotes}
                setProppNotes={setProppNotes}
              />
            )}

            {activeTab === "narrative" && (
              <NarrativeAndBiasSection
                narrativeStructure={narrativeStructure}
                setNarrativeStructure={setNarrativeStructure}
                crossValidation={crossValidation}
                setCrossValidation={setCrossValidation}
              />
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

function MotifSection({ motif, setMotif }) {
  const handleArchetypesChange = (e) => {
    setMotif({
      ...motif,
      character_archetypes: multiSelectFromEvent(e)
    });
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
      <h2>Motif & characters</h2>
      <div className="grid-3">
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
        <label>
          Helper type
          <input
            value={motif.helper_type}
            onChange={(e) =>
              setMotif({ ...motif, helper_type: e.target.value })
            }
            placeholder="CAPTIVE_MAIDEN_AND_ANIMAL"
          />
        </label>
        <label>
          Obstacle thrower (text)
          <input
            value={motif.obstacle_thrower}
            onChange={(e) =>
              setMotif({ ...motif, obstacle_thrower: e.target.value })
            }
          />
        </label>
      </div>

      <label>
        Character archetypes
        <select
          multiple
          value={motif.character_archetypes}
          onChange={handleArchetypesChange}
        >
          {CHARACTER_ARCHETYPES.map((c) => (
            <option key={c} value={c}>
              {c}
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

function DeepAnnotationSection({
  paragraphSummaries,
  setParagraphSummaries,
  proppFns,
  setProppFns,
  proppNotes,
  setProppNotes
}) {
  const handleParagraphChange = (index, value) => {
    const next = [...paragraphSummaries];
    next[index] = value;
    setParagraphSummaries(next);
  };

  const addParagraph = () => {
    setParagraphSummaries([...paragraphSummaries, ""]);
  };

  const handleProppChange = (idx, field, value) => {
    const next = proppFns.map((item, i) =>
      i === idx
        ? {
            ...item,
            [field]:
              field === "span"
                ? { ...item.span, ...value }
                : field === "fn"
                ? value
                : value
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
      <h2>Deep annotation (paragraphs & Propp functions)</h2>

      <div className="section-header-row">
        <span>Paragraph summaries</span>
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

      <hr />

      <div className="section-header-row">
        <span>Propp functions</span>
        <button type="button" className="ghost-btn" onClick={addPropp}>
          + Add function
        </button>
      </div>

      {proppFns.map((fnObj, idx) => (
        <div key={idx} className="propp-row">
          <div className="grid-3">
            <label>
              Function
              <select
                value={fnObj.fn}
                onChange={(e) =>
                  handleProppChange(idx, "fn", e.target.value)
                }
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
              Span start (paragraph index)
              <input
                type="number"
                value={fnObj.span.start}
                onChange={(e) =>
                  handleProppChange(idx, "span", {
                    start: Number(e.target.value)
                  })
                }
              />
            </label>
            <label>
              Span end (paragraph index)
              <input
                type="number"
                value={fnObj.span.end}
                onChange={(e) =>
                  handleProppChange(idx, "span", {
                    end: Number(e.target.value)
                  })
                }
              />
            </label>
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
  setCrossValidation
}) {
  const handleNarrativeChange = (idx, value) => {
    const next = [...narrativeStructure];
    next[idx] = value;
    setNarrativeStructure(next);
  };

  const addNarrative = () => {
    setNarrativeStructure([...narrativeStructure, ""]);
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
      <h2>Narrative structure & bias reflection</h2>

      <div className="section-header-row">
        <span>Narrative structure steps</span>
        <button type="button" className="ghost-btn" onClick={addNarrative}>
          + Add step
        </button>
      </div>
      {narrativeStructure.map((step, idx) => (
        <input
          key={idx}
          value={step}
          onChange={(e) => handleNarrativeChange(idx, e.target.value)}
          placeholder="departure_and_meeting_helper"
        />
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


