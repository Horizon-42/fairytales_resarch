import React, { useMemo } from "react";

export default function SummariesSection({ paragraphSummaries, setParagraphSummaries, sourceText, highlightedRanges, setHighlightedRanges }) {
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
      currentIndex += len + 1;
    });
    return paras;
  }, [sourceText]);

  const { perParagraph = {}, combined = [], whole = "" } = paragraphSummaries;

  const summaryFocus = highlightedRanges ? highlightedRanges["summary-focus"] : null;

  const isSummaryFocusRange = (range) => {
    if (!range) return false;
    if (!summaryFocus) return false;
    return summaryFocus.start === range.start && summaryFocus.end === range.end;
  };

  const getCombinedCharRange = (item) => {
    if (!item) return null;
    const pStart = Math.min(item.start_para, item.end_para);
    const pEnd = Math.max(item.start_para, item.end_para);

    let startChar = Infinity;
    let endChar = -Infinity;

    for (let i = pStart; i <= pEnd; i++) {
      const p = textParagraphs[i];
      if (p) {
        startChar = Math.min(startChar, p.start);
        endChar = Math.max(endChar, p.end);
      }
    }

    if (startChar === Infinity) return null;
    return { start: startChar, end: endChar };
  };

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

  const setSummaryFocus = (range, { toggle = false } = {}) => {
    if (!setHighlightedRanges || !range) return;

    setHighlightedRanges(prev => {
      const next = { ...prev };
      const existing = next["summary-focus"];
      const isSameRange =
        existing &&
        typeof existing.start === "number" &&
        typeof existing.end === "number" &&
        existing.start === range.start &&
        existing.end === range.end;

      if (toggle && isSameRange) {
        delete next["summary-focus"];
        return next;
      }

      next["summary-focus"] = {
        start: range.start,
        end: range.end,
        color: "#86efac"
      };
      return next;
    });
  };

  const focusParagraph = (para, { toggle = false } = {}) => {
    if (!para) return;
    setSummaryFocus({ start: para.start, end: para.end }, { toggle });
  };

  const focusCombined = (item, { toggle = false } = {}) => {
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

    if (startChar !== Infinity) {
      setSummaryFocus({ start: startChar, end: endChar }, { toggle });
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
          const paraRange = { start: para.start, end: para.end };
          const paraIsFocused = isSummaryFocusRange(paraRange);

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
                  style={{
                    padding: "2px 6px",
                    fontSize: "0.7rem",
                    background: paraIsFocused ? "#86efac" : undefined,
                    color: paraIsFocused ? "#000" : undefined,
                    fontWeight: paraIsFocused ? "bold" : undefined
                  }}
                  onClick={() => focusParagraph(para, { toggle: true })}
                >
                  {paraIsFocused ? "Hide" : "Highlight"}
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
                onFocus={() => focusParagraph(para, { toggle: false })}
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

          let charStart = relevantParas[0]?.start ?? 0;
          let charEnd = relevantParas[relevantParas.length - 1]?.end ?? 0;
          const combinedRange = getCombinedCharRange(item);
          const combinedIsFocused = combinedRange ? isSummaryFocusRange(combinedRange) : false;

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
                  style={{
                    padding: "2px 6px",
                    fontSize: "0.7rem",
                    marginLeft: "auto",
                    background: combinedIsFocused ? "#86efac" : undefined,
                    color: combinedIsFocused ? "#000" : undefined,
                    fontWeight: combinedIsFocused ? "bold" : undefined
                  }}
                  onClick={() => focusCombined(item, { toggle: true })}
                >
                  {combinedIsFocused ? "Hide" : "Highlight"}
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
                onFocus={() => focusCombined(item, { toggle: false })}
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

