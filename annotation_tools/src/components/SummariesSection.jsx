import React, { useMemo } from "react";
import { deriveTextSectionsFromNarratives } from "../utils/summarySections.js";

export default function SummariesSection({
  paragraphSummaries,
  setParagraphSummaries,
  sourceText,
  sourceLanguage,
  narrativeStructure,
  highlightedRanges,
  setHighlightedRanges,
  onAutoSummarize,
  autoSummariesLoading,
  autoSummariesProgress
}) {
  const textSections = useMemo(() => {
    if (!sourceText) return [];
    return deriveTextSectionsFromNarratives(narrativeStructure, sourceText);
  }, [narrativeStructure, sourceText]);

  const { perSection = {}, combined = [], whole = "" } = paragraphSummaries;

  const summaryFocus = highlightedRanges ? highlightedRanges["summary-focus"] : null;

  const isSummaryFocusRange = (range) => {
    if (!range) return false;
    if (!summaryFocus) return false;
    return summaryFocus.start === range.start && summaryFocus.end === range.end;
  };

  const getCombinedCharRange = (item) => {
    if (!item) return null;
    const a = item.start_section;
    const b = item.end_section;
    if (!a || !b) return null;

    const startIdx = textSections.findIndex(s => s.text_section === a);
    const endIdx = textSections.findIndex(s => s.text_section === b);
    if (startIdx === -1 || endIdx === -1) return null;

    const lo = Math.min(startIdx, endIdx);
    const hi = Math.max(startIdx, endIdx);

    let startChar = Infinity;
    let endChar = -Infinity;

    for (let i = lo; i <= hi; i++) {
      const s = textSections[i];
      if (s && typeof s.start === "number" && typeof s.end === "number") {
        startChar = Math.min(startChar, s.start);
        endChar = Math.max(endChar, s.end);
      }
    }

    if (startChar === Infinity) return null;
    return { start: startChar, end: endChar };
  };

  const updatePerSection = (key, value) => {
    setParagraphSummaries(prev => ({
      ...prev,
      perSection: { ...prev.perSection, [key]: value }
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
    const first = textSections[0]?.text_section || "";
    setParagraphSummaries(prev => ({
      ...prev,
      combined: [...(prev.combined || []), { start_section: first, end_section: first, text: "" }]
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
    const range = getCombinedCharRange(item);
    if (range) setSummaryFocus(range, { toggle });
  };

  return (
    <section className="card">
      <div className="section-header-row" style={{ alignItems: "center" }}>
        <h2 style={{ margin: 0 }}>Summaries</h2>
        <div style={{ display: "flex", gap: "0.5rem", marginLeft: "auto" }}>
          {autoSummariesLoading && autoSummariesProgress && (
            <span style={{ fontSize: "0.8rem", color: "#6b7280", alignSelf: "center" }}>
              {autoSummariesProgress.done}/{autoSummariesProgress.total}
            </span>
          )}
          <button
            type="button"
            className="ghost-btn"
            onClick={() => onAutoSummarize && onAutoSummarize()}
            disabled={!onAutoSummarize || autoSummariesLoading || !sourceText || !sourceText.trim()}
            title={
              sourceLanguage && sourceLanguage.toLowerCase() === "en"
                ? "Auto-generate English summaries"
                : "Auto-generate bilingual (source language + English) summaries"
            }
          >
            {autoSummariesLoading ? "Auto Summary..." : "Auto Summary"}
          </button>
        </div>
      </div>

      {/* Section 1: Per-Section Summaries */}
      <div style={{ marginBottom: "1.5rem" }}>
        <div className="section-header-row">
          <span style={{ fontWeight: "bold" }}>Per-Section Summaries</span>
          <span style={{ fontSize: "0.75rem", color: "#6b7280" }}>({textSections.length} sections)</span>
        </div>

        {textSections.length === 0 && (
          <p className="hint">No narratives with text_span found.</p>
        )}

        {textSections.map((sec, idx) => {
          const previewRaw = (sec.text || "").replace(/\s+/g, " ").trim();
          const preview = previewRaw.length > 60 ? previewRaw.substring(0, 60) + "..." : previewRaw;
          const summaryText = perSection[sec.text_section] || "";
          const secRange = (typeof sec.start === "number" && typeof sec.end === "number")
            ? { start: sec.start, end: sec.end }
            : null;
          const secIsFocused = secRange ? isSummaryFocusRange(secRange) : false;

          return (
            <div key={idx} style={{ marginBottom: "0.75rem", border: "1px solid #e5e7eb", padding: "0.5rem", borderRadius: "4px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.25rem" }}>
                <span style={{ fontWeight: "bold", fontSize: "0.8rem" }}>
                  Section {idx + 1}
                  <span style={{ fontWeight: "normal", color: "#6b7280", marginLeft: "0.5rem" }}>
                    (text_section: {sec.text_section})
                  </span>
                  {secRange && (
                    <span style={{ fontWeight: "normal", color: "#6b7280", marginLeft: "0.5rem" }}>
                      ({secRange.start}-{secRange.end})
                    </span>
                  )}
                </span>
                <button
                  type="button"
                  className="ghost-btn"
                  style={{
                    padding: "2px 6px",
                    fontSize: "0.7rem",
                    background: secIsFocused ? "#86efac" : undefined,
                    color: secIsFocused ? "#000" : undefined,
                    fontWeight: secIsFocused ? "bold" : undefined
                  }}
                  onClick={() => secRange && setSummaryFocus(secRange, { toggle: true })}
                  disabled={!secRange}
                >
                  {secIsFocused ? "Hide" : "Highlight"}
                </button>
              </div>
              <div style={{ fontSize: "0.7rem", color: "#666", marginBottom: "0.25rem", fontStyle: "italic", background: "#f9fafb", padding: "0.25rem", borderRadius: "2px" }}>
                "{preview || "(no text_span range to preview)"}"
              </div>
              <textarea
                rows={2}
                value={summaryText}
                onChange={(e) => updatePerSection(sec.text_section, e.target.value)}
                placeholder={`Summary for section ${idx + 1}...`}
                style={{ width: "100%", fontSize: "0.85rem" }}
                onFocus={() => secRange && setSummaryFocus(secRange, { toggle: false })}
              />
            </div>
          );
        })}
      </div>

      <hr />

      {/* Section 2: Combined Section Summaries */}
      <div style={{ marginBottom: "1.5rem" }}>
        <div className="section-header-row">
          <span style={{ fontWeight: "bold" }}>Combined Section Summaries</span>
        </div>

        {combined.length === 0 && (
          <p className="hint">No combined summaries. Use the button below to add one.</p>
        )}

        {combined.map((item, idx) => {
          const combinedRange = getCombinedCharRange(item);
          const combinedIsFocused = combinedRange ? isSummaryFocusRange(combinedRange) : false;
          const preview = (() => {
            if (!combinedRange) return "Invalid Range";
            const raw = (sourceText || "").slice(combinedRange.start, combinedRange.end);
            const cleaned = raw.replace(/\s+/g, " ").trim();
            return cleaned.length > 80 ? cleaned.substring(0, 80) + "..." : cleaned;
          })();

          return (
            <div key={idx} style={{ marginBottom: "0.75rem", border: "1px solid #d1d5db", padding: "0.5rem", borderRadius: "4px", background: "#fefce8" }}>
              <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", marginBottom: "0.5rem" }}>
                <span style={{ fontWeight: "bold", fontSize: "0.8rem" }}>Range:</span>
                <label style={{ fontSize: "0.8rem" }}>
                  Start:
                  <select
                    value={item.start_section || ""}
                    onChange={(e) => updateCombined(idx, "start_section", e.target.value)}
                    style={{ marginLeft: "0.25rem" }}
                  >
                    {textSections.map(s => (
                      <option key={s.text_section} value={s.text_section}>{s.text_section}</option>
                    ))}
                  </select>
                </label>
                <label style={{ fontSize: "0.8rem" }}>
                  End:
                  <select
                    value={item.end_section || ""}
                    onChange={(e) => updateCombined(idx, "end_section", e.target.value)}
                    style={{ marginLeft: "0.25rem" }}
                  >
                    {textSections.map(s => (
                      <option key={s.text_section} value={s.text_section}>{s.text_section}</option>
                    ))}
                  </select>
                </label>
                {combinedRange && (
                  <span style={{ fontSize: "0.75rem", color: "#6b7280" }}>
                    (chars: {combinedRange.start}-{combinedRange.end})
                  </span>
                )}
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
                Preview: "{preview}"
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

