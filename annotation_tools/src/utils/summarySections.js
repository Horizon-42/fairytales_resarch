// Utilities for building Summary-tab segments from narrative events.
// Segmentation rule: derive sections ONLY from narratives' `text_span`.
// - Each unique (start,end) becomes a section.
// - Section key is `S{start}-{end}`.
// - Sections are ordered by start then end.

export function deriveTextSectionsFromNarratives(narrativeStructure, fullText) {
  const text = typeof fullText === "string" ? fullText : "";
  const events = Array.isArray(narrativeStructure) ? narrativeStructure : [];

  // Keep insertion order of first appearance.
  const sectionMap = new Map(); // key -> { key, start, end, firstOrder, narrativeNumbers:Set<number> }

  for (let i = 0; i < events.length; i++) {
    const evt = events[i];
    if (!evt || typeof evt !== "object") continue;

    const start = evt.text_span && typeof evt.text_span.start === "number" ? evt.text_span.start : null;
    const end = evt.text_span && typeof evt.text_span.end === "number" ? evt.text_span.end : null;

    // We only use text_span to identify sections.
    if (typeof start !== "number" || typeof end !== "number") continue;

    // Normalize / clamp to text boundaries.
    const safeStart = Math.max(0, Math.min(text.length, start));
    const safeEnd = Math.max(0, Math.min(text.length, end));
    if (safeEnd <= safeStart) continue;

    const key = `S${safeStart}-${safeEnd}`;

    const sectionBounds = { start: safeStart, end: safeEnd };

    if (!sectionMap.has(key)) {
      sectionMap.set(key, {
        key,
        start: sectionBounds.start,
        end: sectionBounds.end,
        firstOrder: typeof evt.time_order === "number" ? evt.time_order : i,
        narrativeNumbers: new Set([
          typeof evt.time_order === "number" ? evt.time_order : (i + 1)
        ])
      });
    } else {
      const acc = sectionMap.get(key);
      const startToUse = sectionBounds.start;
      const endToUse = sectionBounds.end;
      if (typeof startToUse === "number") {
        acc.start = typeof acc.start === "number" ? Math.min(acc.start, startToUse) : startToUse;
      }
      if (typeof endToUse === "number") {
        acc.end = typeof acc.end === "number" ? Math.max(acc.end, endToUse) : endToUse;
      }
      if (typeof evt.time_order === "number") {
        acc.firstOrder = Math.min(acc.firstOrder, evt.time_order);
      }

      const n = typeof evt.time_order === "number" ? evt.time_order : (i + 1);
      if (typeof n === "number" && Number.isFinite(n)) {
        acc.narrativeNumbers.add(n);
      }
    }
  }

  const sections = Array.from(sectionMap.values());

  // Primary sort: by extracted span start; fallback to time_order/insertion.
  sections.sort((a, b) => {
    const aStart = typeof a.start === "number" ? a.start : Infinity;
    const bStart = typeof b.start === "number" ? b.start : Infinity;
    if (aStart !== bStart) return aStart - bStart;
    return (a.firstOrder ?? 0) - (b.firstOrder ?? 0);
  });

  return sections.map((s) => {
    const start = typeof s.start === "number" ? Math.max(0, Math.min(text.length, s.start)) : null;
    const end = typeof s.end === "number" ? Math.max(0, Math.min(text.length, s.end)) : null;

    let sectionText = "";
    if (start != null && end != null && end > start) {
      sectionText = text.slice(start, end);
    }

    const narrative_numbers = Array.from(s.narrativeNumbers || [])
      .filter((n) => typeof n === "number" && Number.isFinite(n))
      .sort((a, b) => a - b);
    const display_label = narrative_numbers.length > 0
      ? `N${narrative_numbers.join(",")}`
      : s.key;

    return {
      text_section: s.key,
      display_label,
      narrative_numbers,
      start,
      end,
      text: sectionText
    };
  });
}
