import React from "react";

export default function StoryMetadata({
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
}) {
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

