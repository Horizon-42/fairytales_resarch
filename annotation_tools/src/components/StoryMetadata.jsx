import React from "react";

// Map culture to relevant languages
const CULTURE_LANGUAGES = {
  "Persian": [
    { value: "fa", label: "Persian (Farsi)" },
    { value: "en", label: "English" }
  ],
  "Chinese": [
    { value: "zh", label: "Chinese" },
    { value: "en", label: "English" }
  ],
  "Indian": [
    { value: "hi", label: "Hindi" },
    { value: "en", label: "English" },
    { value: "sa", label: "Sanskrit" }
  ],
  "Arabic": [
    { value: "ar", label: "Arabic" },
    { value: "en", label: "English" }
  ],
  "Turkish": [
    { value: "tr", label: "Turkish" },
    { value: "en", label: "English" }
  ]
};

export default function StoryMetadata({
  id,
  culture,
  title,
  onChangeId,
  onChangeCulture,
  onChangeTitle,
  sourceText,
  setSourceText
}) {
  // Get relevant languages for current culture, default to English if culture not found
  const availableLanguages = CULTURE_LANGUAGES[culture] || [
    { value: "en", label: "English" }
  ];
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

      <div className="grid-2">
        <label>
          Source language (optional)
          <select
            value={sourceText.language || ""}
            onChange={(e) =>
              setSourceText({ ...sourceText, language: e.target.value })
            }
          >
            <option value="">– Select language (optional) –</option>
            {availableLanguages.map((lang) => (
              <option key={lang.value} value={lang.value}>
                {lang.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Source type (optional)
          <select
            value={sourceText.type || ""}
            onChange={(e) =>
              setSourceText({ ...sourceText, type: e.target.value })
            }
          >
            <option value="">– Select type (optional) –</option>
            <option value="summary">Summary</option>
            <option value="full_text">Full text</option>
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
          type="text"
          value={sourceText.reference_uri || ""}
          readOnly
          style={{ backgroundColor: "#f3f4f6", cursor: "not-allowed" }}
          placeholder="Will be auto-filled from selected text file"
        />
      </label>
    </section>
  );
}

