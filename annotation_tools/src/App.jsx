import React, { useMemo, useState, useEffect, useRef } from "react";
import { organizeFiles, mapV1ToState, mapV2ToState, generateUUID } from "./utils/fileHandler.js";
import { downloadJson, relPathToDatasetHint, HIGHLIGHT_COLORS, emptyProppFn, extractEnglishFromRelationship, buildActionLayer } from "./utils/helpers.js";
import { saveFolderCache, loadFolderCache, extractFolderPath } from "./utils/folderCache.js";
import { getBackendUrl, clearBackendCache } from "./utils/backendConfig.js";
import { deriveTextSectionsFromNarratives } from "./utils/summarySections.js";

// Import components
import {
  StoryBrowser,
  StoryMetadata,
  EndingAndValuesSection,
  CharacterSection,
  MotifSection,
  SummariesSection,
  ProppSection,
  NarrativeSection,
  QASection,
  ContextMenu
} from "./components";

export default function App() {
  // ========== State Management ==========
  const [storyFiles, setStoryFiles] = useState([]);
  const [v1JsonFiles, setV1JsonFiles] = useState({});
  const [v2JsonFiles, setV2JsonFiles] = useState({});
  const [selectedStoryIndex, setSelectedStoryIndex] = useState(-1);
  const [currentSelection, setCurrentSelection] = useState(null);

  const [jsonSaveHint, setJsonSaveHint] = useState(
    "datasets/iron/persian/persian/json/FA_XXX.json"
  );
  const [showPreview, setShowPreview] = useState(false);
  const [previewVersion, setPreviewVersion] = useState("v2");

  const [id, setId] = useState("FA_XXX");
  // Initialize culture from cache if available
  const [culture, setCulture] = useState(() => {
    const cache = loadFolderCache();
    return cache?.culture || "Persian";
  });
  const [title, setTitle] = useState("");

  // Extract title from ID (everything after the second underscore)
  const extractTitleFromId = (taleId) => {
    if (!taleId) return "";
    const parts = taleId.split("_");
    if (parts.length > 2) {
      // Return everything after the second underscore
      return parts.slice(2).join("_");
    }
    return "";
  };

  // Handle ID change and auto-extract title
  const handleIdChange = (newId) => {
    setId(newId);
    const extractedTitle = extractTitleFromId(newId);
    setTitle(extractedTitle);
  };

  const [sourceText, setSourceText] = useState({
    text: "",
    language: "en",
    type: "summary",
    reference_uri: ""
  });

  const [meta, setMeta] = useState({
    main_motif: "",
    atu_type: "",
    ending_type: "HAPPY_REUNION",
    key_values: [],
    target_motif: true
  });

  const [motif, setMotif] = useState({
    atu_type: "",
    atu_categories: [],
    motif_type: [],
    character_archetypes: [],
    obstacle_pattern: [],
    obstacle_thrower: [],
    helper_type: [],
    thinking_process: "",
    atu_evidence: {},
    motif_evidence: {}
  });

  const [paragraphSummaries, setParagraphSummaries] = useState({
    perSection: {},
    combined: [],
    whole: ""
  });
  const [proppFns, setProppFns] = useState([emptyProppFn()]);
  const [proppNotes, setProppNotes] = useState("");

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

  const [activeTab, setActiveTab] = useState("characters");
  const [highlightedChars, setHighlightedChars] = useState({});
  const [highlightedRanges, setHighlightedRanges] = useState({});
  const [lastAutoSave, setLastAutoSave] = useState(null);
  const [newlyCreatedCharacterIndex, setNewlyCreatedCharacterIndex] = useState(null);
  const [autoAnnotateCharactersLoading, setAutoAnnotateCharactersLoading] = useState(false);
  const [autoAnnotateEventLoading, setAutoAnnotateEventLoading] = useState({});
  const [autoSummariesLoading, setAutoSummariesLoading] = useState(false);
  const [autoSummariesProgress, setAutoSummariesProgress] = useState({ done: 0, total: 0 });
  const [autoDetectMotifLoading, setAutoDetectMotifLoading] = useState(false);
  const [autoSegmentNarrativesLoading, setAutoSegmentNarrativesLoading] = useState(false);

  // Context menu state
  const [contextMenu, setContextMenu] = useState({ visible: false, x: 0, y: 0 });

  const handleAutoAnnotateCharacters = async (mode = "recreate", additionalPrompt = "") => {
    if (autoAnnotateCharactersLoading) return;
    if (!sourceText?.text || !sourceText.text.trim()) {
      alert("No story text loaded.");
      return;
    }

    setAutoAnnotateCharactersLoading(true);
    try {
      const backendUrl = await getBackendUrl();
      
      // Prepare existing characters data for incremental annotation
      const existingCharacters = mode !== "recreate" ? {
        character_archetypes: motif.character_archetypes || [],
        helper_type: motif.helper_type || [],
        obstacle_thrower: motif.obstacle_thrower || []
      } : null;

      const resp = await fetch(`${backendUrl}/api/annotate/characters`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: sourceText.text,
          culture,
          existing_characters: existingCharacters,
          mode: mode,
          additional_prompt: additionalPrompt || null
        })
      });

      const data = await resp.json().catch(() => null);
      if (!resp.ok || !data?.ok) {
        const msg = (data && (data.detail || data.error)) ? (data.detail || data.error) : `HTTP ${resp.status}`;
        throw new Error(msg);
      }

      if (data.motif && typeof data.motif === "object") {
        setMotif((prev) => ({ ...prev, ...data.motif }));
      }
    } catch (err) {
      console.error("Auto-annotate characters failed:", err);
      alert(`Auto-annotate failed: ${err?.message || err}`);
    } finally {
      setAutoAnnotateCharactersLoading(false);
    }
  };

  const handleAutoAnnotateEvent = async (eventId, eventIndex, mode = "recreate", additionalPrompt = "") => {
    if (autoAnnotateEventLoading[eventId]) return;
    if (!sourceText?.text || !sourceText.text.trim()) {
      alert("No story text loaded.");
      return;
    }

    setAutoAnnotateEventLoading((prev) => ({ ...prev, [eventId]: true }));
    try {
      const backendUrl = await getBackendUrl();

      const characterList = Array.isArray(motif.character_archetypes)
        ? motif.character_archetypes.map(c => typeof c === "string" ? c : c.name).filter(Boolean)
        : [];

      const currentEvent = narrativeStructure.find(n => typeof n === "object" && n.id === eventId);
      if (!currentEvent) throw new Error("Event not found in narrative structure");

      // history_events: events that occurred earlier (based on time_order)
      const historyEvents = narrativeStructure
        .filter(n => typeof n === "object" && n.id !== eventId && n.time_order < (currentEvent.time_order || Infinity))
        .sort((a, b) => (a.time_order || 0) - (b.time_order || 0));

      const resp = await fetch(`${backendUrl}/api/annotate/narrative`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          narrative_id: eventId,
          text_span: currentEvent.text_span || { start: 0, end: sourceText.text.length, text: sourceText.text.substring(0, 100) },
          narrative_text: sourceText.text,
          character_list: characterList,
          culture: culture,
          existing_event: mode !== "recreate" ? currentEvent : null,
          history_events: historyEvents.length > 0 ? historyEvents : null,
          mode: mode,
          additional_prompt: additionalPrompt || null
        })
      });

      const data = await resp.json().catch(() => null);
      if (!resp.ok || !data?.ok) {
        const msg = (data && (data.detail || data.error)) ? (data.detail || data.error) : `HTTP ${resp.status}`;
        throw new Error(msg);
      }

      if (data.event && typeof data.event === "object") {
        setNarrativeStructure((prev) => {
          const next = [...prev];
          const idx = next.findIndex(n => typeof n === "object" && n.id === eventId);
          if (idx !== -1) {
            next[idx] = { ...next[idx], ...data.event };
          }
          return next;
        });
      }
    } catch (err) {
      console.error("Auto-annotate event failed:", err);
      alert(`Auto-annotate failed: ${err?.message || err}`);
    } finally {
      setAutoAnnotateEventLoading((prev) => {
        const next = { ...prev };
        delete next[eventId];
        return next;
      });
    }
  };

  const handleAutoSegmentNarratives = async (mode = "embedding_assisted") => {
    if (autoSegmentNarrativesLoading) return;
    if (!sourceText?.text || !sourceText.text.trim()) {
      alert("No story text loaded.");
      return;
    }

    setAutoSegmentNarrativesLoading(true);
    try {
      const backendUrl = await getBackendUrl();

      const resp = await fetch(`${backendUrl}/api/narrative/auto_segment`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: sourceText.text,
          culture: culture,
          mode: mode
        })
      });

      const data = await resp.json().catch(() => null);
      if (!resp.ok || !data?.ok) {
        const msg = (data && (data.detail || data.error)) ? (data.detail || data.error) : `HTTP ${resp.status}`;
        throw new Error(msg);
      }

      const events = Array.isArray(data.narrative_events) ? data.narrative_events : [];
      if (events.length === 0) {
        alert("Auto-segmentation returned no segments.");
        return;
      }

      setNarrativeStructure(events);
    } catch (err) {
      console.error("Auto-segment narratives failed:", err);
      alert(`Auto-segmentation failed: ${err?.message || err}`);
    } finally {
      setAutoSegmentNarrativesLoading(false);
    }
  };

  const handleAutoSummarize = async () => {
    if (autoSummariesLoading) return;
    if (!sourceText?.text || !sourceText.text.trim()) {
      alert("No story text loaded.");
      return;
    }

    setAutoSummariesLoading(true);
    setAutoSummariesProgress({ done: 0, total: 0 });
    try {
      const backendUrl = await getBackendUrl();

      const sections = deriveTextSectionsFromNarratives(narrativeStructure, sourceText.text);
      if (sections.length === 0) {
        alert("No narratives with text_span found to build sections.");
        return;
      }
      setAutoSummariesProgress({ done: 0, total: sections.length });

      // Clear existing per-section summaries first (keep combined).
      setParagraphSummaries(prev => ({ ...prev, perSection: {}, whole: "" }));

      const lang = sourceText.language || "en";

      // Generate per-section summaries incrementally.
      const perSectionLocal = {};
      for (let i = 0; i < sections.length; i++) {
        const sectionKey = sections[i]?.text_section || String(i);
        const sectionText = sections[i]?.text || "";
        const resp = await fetch(`${backendUrl}/api/annotate/summaries/paragraph`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            index: i,
            paragraph: sectionText,
            language: lang,
            model: "qwen3:8b"
          })
        });

        const data = await resp.json().catch(() => null);
        if (!resp.ok || !data?.ok) {
          const msg = (data && (data.detail || data.error)) ? (data.detail || data.error) : `HTTP ${resp.status}`;
          throw new Error(msg);
        }

        const text = data.text || "";
        perSectionLocal[String(sectionKey)] = text;
        setParagraphSummaries(prev => ({
          ...prev,
          perSection: { ...(prev.perSection || {}), [String(sectionKey)]: text }
        }));
        setAutoSummariesProgress(prev => ({ ...prev, done: Math.min(prev.total, prev.done + 1) }));
      }

      // Now request whole-story summary based on the per-paragraph summaries.
      const respWhole = await fetch(`${backendUrl}/api/annotate/summaries/whole`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          per_section: perSectionLocal,
          language: lang,
          model: "qwen3:8b"
        })
      });

      const dataWhole = await respWhole.json().catch(() => null);
      if (!respWhole.ok || !dataWhole?.ok) {
        const msg = (dataWhole && (dataWhole.detail || dataWhole.error)) ? (dataWhole.detail || dataWhole.error) : `HTTP ${respWhole.status}`;
        throw new Error(msg);
      }

      setParagraphSummaries(prev => ({
        ...prev,
        whole: dataWhole.whole || ""
      }));
    } catch (err) {
      console.error("Auto-summary failed:", err);
      alert(`Auto-summary failed: ${err?.message || err}`);
    } finally {
      setAutoSummariesLoading(false);
    }
  };

  const handleAutoDetectMotifAtu = async () => {
    if (autoDetectMotifLoading) return;
    if (!sourceText?.text || !sourceText.text.trim()) {
      alert("No story text loaded.");
      return;
    }

    setAutoDetectMotifLoading(true);
    try {
      const backendUrl = await getBackendUrl();

      const per = paragraphSummaries?.perSection || {};
      const sections = deriveTextSectionsFromNarratives(narrativeStructure, sourceText.text);
      const whole = (paragraphSummaries?.whole || "").trim();

      const detectOnce = async (text) => {
        const resp = await fetch(`${backendUrl}/api/detect/motif_atu`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            text,
            top_k: 10
          })
        });

        const data = await resp.json().catch(() => null);
        if (!resp.ok || !data?.ok) {
          const msg = (data && (data.detail || data.error)) ? (data.detail || data.error) : `HTTP ${resp.status}`;
          throw new Error(msg);
        }
        return data;
      };

      const sectionCandidates = sections
        .map((s) => {
          const key = String(s.text_section);
          const summary = per[key];
          return { key, summary };
        })
        .filter((x) => typeof x.summary === "string" && x.summary.trim());

      const WHOLE_SUMMARY_KEY = "__WHOLE_SUMMARY__";

      const bestAtu = {};
      const bestMotif = {};

      const recordBest = (bestMap, label, similarity, sectionKey) => {
        if (!label) return;
        const prev = bestMap[label];
        if (!prev || similarity > prev.similarity) {
          bestMap[label] = { similarity, sectionKey };
        }
      };

      // Prefer section-summary-based evidence. We detect per section, then choose the section
      // with the highest similarity as evidence for each label.
      if (sectionCandidates.length > 0) {
        // Cap requests to avoid overwhelming backend on very long stories.
        const MAX_SECTION_DETECT = 30;
        const picked = sectionCandidates
          .slice()
          .sort((a, b) => (b.summary.length || 0) - (a.summary.length || 0))
          .slice(0, MAX_SECTION_DETECT);

        const results = await Promise.all(
          picked.map(async ({ key, summary }) => {
            const data = await detectOnce(summary);
            return { key, data };
          })
        );

        results.forEach(({ key, data }) => {
          (Array.isArray(data.atu) ? data.atu : []).forEach((item) => {
            recordBest(bestAtu, item?.label, Number(item?.similarity || 0), key);
          });
          (Array.isArray(data.motifs) ? data.motifs : []).forEach((item) => {
            recordBest(bestMotif, item?.label, Number(item?.similarity || 0), key);
          });
        });
      }

      // Also run once on whole summary (if available) to recover global labels.
      // Evidence will still prefer a best section match; otherwise it falls back to whole.
      let wholeData = null;
      if (whole) {
        wholeData = await detectOnce(whole);
      }

      const mergeLabels = (bestMap, listFromWhole) => {
        const labels = Object.keys(bestMap);
        (Array.isArray(listFromWhole) ? listFromWhole : []).forEach((item) => {
          const label = item?.label;
          if (label && !labels.includes(label)) labels.push(label);
        });
        // Sort by best similarity when we have it; otherwise put at the end.
        labels.sort((a, b) => {
          const sa = bestMap[a]?.similarity ?? -1;
          const sb = bestMap[b]?.similarity ?? -1;
          return sb - sa;
        });
        return labels.slice(0, 10);
      };

      const atuLabels = mergeLabels(bestAtu, wholeData?.atu);
      const motifLabels = mergeLabels(bestMotif, wholeData?.motifs);

      const evidenceKeyForLabel = (bestMap, label) => {
        const best = bestMap[label];
        if (best?.sectionKey) return best.sectionKey;
        if (whole) return WHOLE_SUMMARY_KEY;
        const firstSectionKey = sections && sections.length > 0 ? String(sections[0].text_section) : "";
        return firstSectionKey || "";
      };

      setMotif(prev => {
        const prevAtu = Array.isArray(prev.atu_categories) ? prev.atu_categories : (prev.atu_categories ? [prev.atu_categories] : []);
        const prevMotifs = Array.isArray(prev.motif_type) ? prev.motif_type : (prev.motif_type ? [prev.motif_type] : []);

        const prevAtuEvidence = (prev.atu_evidence && typeof prev.atu_evidence === "object") ? prev.atu_evidence : {};
        const prevMotifEvidence = (prev.motif_evidence && typeof prev.motif_evidence === "object") ? prev.motif_evidence : {};
        const nextAtuEvidence = { ...prevAtuEvidence };
        const nextMotifEvidence = { ...prevMotifEvidence };

        const nextAtu = [...prevAtu];
        atuLabels.forEach(l => {
          if (!nextAtu.includes(l)) nextAtu.push(l);
          if (!nextAtuEvidence[l]) {
            const k = evidenceKeyForLabel(bestAtu, l);
            nextAtuEvidence[l] = { evidence_keys: k ? [k] : [] };
          }
        });

        const nextMotifs = [...prevMotifs];
        motifLabels.forEach(l => {
          if (!nextMotifs.includes(l)) nextMotifs.push(l);
          if (!nextMotifEvidence[l]) {
            const k = evidenceKeyForLabel(bestMotif, l);
            nextMotifEvidence[l] = { evidence_keys: k ? [k] : [] };
          }
        });

        return {
          ...prev,
          atu_categories: nextAtu,
          motif_type: nextMotifs,
          atu_evidence: nextAtuEvidence,
          motif_evidence: nextMotifEvidence
        };
      });
    } catch (err) {
      console.error("Auto detect motif/ATU failed:", err);
      alert(`Auto detect failed: ${err?.message || err}`);
    } finally {
      setAutoDetectMotifLoading(false);
    }
  };

  // ========== JSON Builders ==========
  const jsonV1 = useMemo(
    () => ({
      id,
      culture,
      title,
      source_text: sourceText,
      metadata: meta,
      thinking_process: motif.thinking_process || "",
      annotation: {
        motif: (() => {
          const WHOLE_SUMMARY_KEY = "__WHOLE_SUMMARY__";
          const sanitizeEvidenceMap = (src) => {
            const input = (src && typeof src === "object" && !Array.isArray(src)) ? src : {};
            const out = {};
            Object.keys(input).forEach((k) => {
              const v = input[k] || {};
              let keys = [];
              if (Array.isArray(v.evidence_keys)) {
                keys = v.evidence_keys;
              } else {
                const related = Array.isArray(v.related_sections) ? v.related_sections : [];
                const includeWhole = !!v.include_whole_summary;
                keys = [
                  ...(includeWhole ? [WHOLE_SUMMARY_KEY] : []),
                  ...related
                ];
              }
              const uniq = [];
              (Array.isArray(keys) ? keys : []).forEach((ek) => {
                if (!ek) return;
                if (!uniq.includes(ek)) uniq.push(ek);
              });
              out[k] = { evidence_keys: uniq };
            });
            return out;
          };

          return {
            ...motif,
            atu_evidence: sanitizeEvidenceMap(motif.atu_evidence),
            motif_evidence: sanitizeEvidenceMap(motif.motif_evidence)
          };
        })(),
        deep: {
          paragraph_summaries: {
            per_section: paragraphSummaries.perSection || {},
            combined: (paragraphSummaries.combined || []).filter(
              c => c && c.start_section && c.end_section && c.text && c.text.trim()
            ),
            whole: paragraphSummaries.whole || ""
          },
          propp_functions: proppFns.filter((f) => f.fn || f.evidence),
          propp_notes: proppNotes
        }
      },
      narrative_structure: narrativeStructure
        .filter((n) => (typeof n === "string" ? n.trim() : n.event_type))
        .map((n) => {
          if (typeof n !== "object") return n;

          const result = { ...n };

          const agents = Array.isArray(result.agents) ? result.agents.filter(Boolean) : [];
          const targets = Array.isArray(result.targets) ? result.targets.filter(Boolean) : [];
          const isMultiRelationship = result.target_type === "character" && (agents.length > 1 || targets.length > 1);

          const existingMultiList = Array.isArray(result.relationship_multi)
            ? result.relationship_multi
            : ((result.relationship_multi && typeof result.relationship_multi === "object") ? [result.relationship_multi] : []);

          if (isMultiRelationship) {
            const listSource = (existingMultiList.length > 0)
              ? existingMultiList
              : [{
                  agent: agents.length === 1 ? agents[0] : (agents[0] || ""),
                  target: targets.length === 1 ? targets[0] : (targets[0] || ""),
                  relationship_level1: result.relationship_level1 || "",
                  relationship_level2: result.relationship_level2 || "",
                  sentiment: result.sentiment || ""
                }];

            result.relationship_multi = listSource.map((r) => {
              const rel = (r && typeof r === "object") ? r : {};
              const level1 = rel.relationship_level1 || "";
              return {
                agent: rel.agent || "",
                target: rel.target || "",
                relationship_level1: level1 ? extractEnglishFromRelationship(level1) : "",
                relationship_level2: rel.relationship_level2 || "",
                sentiment: rel.sentiment || ""
              };
            });

            // In multi-person cases, keep legacy fields empty to avoid ambiguity
            result.relationship_level1 = "";
            result.relationship_level2 = "";
            // Sentiment becomes per-relationship in multi-person case
            result.sentiment = "";
          } else {
            // Ensure relationship_level1 only contains English
            if (result.relationship_level1) {
              result.relationship_level1 = extractEnglishFromRelationship(result.relationship_level1);
            } else if (existingMultiList[0]?.relationship_level1) {
              // Backward-compat fallback if only relationship_multi exists
              result.relationship_level1 = extractEnglishFromRelationship(existingMultiList[0].relationship_level1);
            }

            if (!result.relationship_level2 && existingMultiList[0]?.relationship_level2) {
              result.relationship_level2 = existingMultiList[0].relationship_level2;
            }

            if (!result.sentiment && existingMultiList[0]?.sentiment) {
              result.sentiment = existingMultiList[0].sentiment;
            }
          }

          // Build action_layer from individual fields
          const actionLayer = buildActionLayer(n);
          if (actionLayer) {
            result.action_layer = actionLayer;
            // Remove individual action fields to avoid duplication
            delete result.action_category;
            delete result.action_type;
            delete result.action_context;
            delete result.action_status;
          }

          return result;
        }),
      cross_validation: crossValidation,
      qa
    }),
    [id, culture, title, sourceText, meta, motif, paragraphSummaries, proppFns, proppNotes, narrativeStructure, crossValidation, qa]
  );

  const jsonV2 = useMemo(() => {
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
        confidence: qa.confidence
      },
      source_info: {
        language: sourceText.language,
        type: sourceText.type,
        reference_uri: sourceText.reference_uri,
        text_content: sourceText.text
      },
      characters: characters,
      narrative_events: narrativeStructure.map((n) => {
        if (typeof n === "string") {
          return { event_type: "OTHER", description: n, narrative_function: "" };
        }

        const result = { ...n };

        const agents = Array.isArray(result.agents) ? result.agents.filter(Boolean) : [];
        const targets = Array.isArray(result.targets) ? result.targets.filter(Boolean) : [];
        const isMultiRelationship = result.target_type === "character" && (agents.length > 1 || targets.length > 1);

        const existingMultiList = Array.isArray(result.relationship_multi)
          ? result.relationship_multi
          : ((result.relationship_multi && typeof result.relationship_multi === "object") ? [result.relationship_multi] : []);

        if (isMultiRelationship) {
          const listSource = (existingMultiList.length > 0)
            ? existingMultiList
            : [{
                agent: agents.length === 1 ? agents[0] : (agents[0] || ""),
                target: targets.length === 1 ? targets[0] : (targets[0] || ""),
                relationship_level1: result.relationship_level1 || "",
                relationship_level2: result.relationship_level2 || "",
                sentiment: result.sentiment || ""
              }];

          result.relationship_multi = listSource.map((r) => {
            const rel = (r && typeof r === "object") ? r : {};
            const level1 = rel.relationship_level1 || "";
            return {
              agent: rel.agent || "",
              target: rel.target || "",
              relationship_level1: level1 ? extractEnglishFromRelationship(level1) : "",
              relationship_level2: rel.relationship_level2 || "",
              sentiment: rel.sentiment || ""
            };
          });

          result.relationship_level1 = "";
          result.relationship_level2 = "";
          result.sentiment = "";
        } else {
          // Ensure relationship_level1 only contains English
          if (result.relationship_level1) {
            result.relationship_level1 = extractEnglishFromRelationship(result.relationship_level1);
          } else if (existingMultiList[0]?.relationship_level1) {
            result.relationship_level1 = extractEnglishFromRelationship(existingMultiList[0].relationship_level1);
          }

          if (!result.relationship_level2 && existingMultiList[0]?.relationship_level2) {
            result.relationship_level2 = existingMultiList[0].relationship_level2;
          }

          if (!result.sentiment && existingMultiList[0]?.sentiment) {
            result.sentiment = existingMultiList[0].sentiment;
          }
        }

        // Build action_layer from individual fields
        const actionLayer = buildActionLayer(n);
        if (actionLayer) {
          result.action_layer = actionLayer;
          // Remove individual action fields to avoid duplication
          delete result.action_category;
          delete result.action_type;
          delete result.action_context;
          delete result.action_status;
        }

        return result;
      }),
      themes_and_motifs: {
        ending_type: meta.ending_type,
        key_values: meta.key_values,
        motif_type: Array.isArray(motif.motif_type) ? motif.motif_type : [],
        atu_categories: Array.isArray(motif.atu_categories) ? motif.atu_categories : [],
        obstacle_thrower: Array.isArray(motif.obstacle_thrower) ? motif.obstacle_thrower : [],
        helper_type: Array.isArray(motif.helper_type) ? motif.helper_type : [],
        thinking_process: motif.thinking_process,
        atu_evidence: (() => {
          const WHOLE_SUMMARY_KEY = "__WHOLE_SUMMARY__";
          const input = (motif.atu_evidence && typeof motif.atu_evidence === "object" && !Array.isArray(motif.atu_evidence))
            ? motif.atu_evidence
            : {};

          const out = {};
          Object.keys(input).forEach((k) => {
            const v = input[k] || {};
            let keys = [];

            if (Array.isArray(v.evidence_keys)) {
              keys = v.evidence_keys;
            } else {
              const related = Array.isArray(v.related_sections) ? v.related_sections : [];
              const includeWhole = !!v.include_whole_summary;
              keys = [
                ...(includeWhole ? [WHOLE_SUMMARY_KEY] : []),
                ...related
              ];
            }

            const uniq = [];
            (Array.isArray(keys) ? keys : []).forEach((ek) => {
              if (!ek) return;
              if (!uniq.includes(ek)) uniq.push(ek);
            });
            out[k] = { evidence_keys: uniq };
          });
          return out;
        })(),
        motif_evidence: (() => {
          const WHOLE_SUMMARY_KEY = "__WHOLE_SUMMARY__";
          const input = (motif.motif_evidence && typeof motif.motif_evidence === "object" && !Array.isArray(motif.motif_evidence))
            ? motif.motif_evidence
            : {};

          const out = {};
          Object.keys(input).forEach((k) => {
            const v = input[k] || {};
            let keys = [];

            if (Array.isArray(v.evidence_keys)) {
              keys = v.evidence_keys;
            } else {
              const related = Array.isArray(v.related_sections) ? v.related_sections : [];
              const includeWhole = !!v.include_whole_summary;
              keys = [
                ...(includeWhole ? [WHOLE_SUMMARY_KEY] : []),
                ...related
              ];
            }

            const uniq = [];
            (Array.isArray(keys) ? keys : []).forEach((ek) => {
              if (!ek) return;
              if (!uniq.includes(ek)) uniq.push(ek);
            });
            out[k] = { evidence_keys: uniq };
          });
          return out;
        })()
      },
      analysis: {
        propp_functions: proppFns.filter((f) => f.fn || f.evidence),
        propp_notes: proppNotes,
        paragraph_summaries: {
          per_section: paragraphSummaries.perSection || {},
          combined: (paragraphSummaries.combined || []).filter(
            c => c && c.start_section && c.end_section && c.text && c.text.trim()
          ),
          whole: paragraphSummaries.whole || ""
        },
        bias_reflection: crossValidation.bias_reflection,
        qa_notes: qa.notes
      }
    };
  }, [id, culture, title, sourceText, meta, motif, paragraphSummaries, proppFns, proppNotes, narrativeStructure, crossValidation, qa]);

  // ========== Save/Load Functions ==========
  const handleSave = async (version, silent = false) => {
    const data = version === "v2" ? jsonV2 : jsonV1;
    const currentStory = storyFiles[selectedStoryIndex];
    
    if (!currentStory) {
      if (!silent) alert("No story selected to save.");
      return;
    }

    try {
      const response = await fetch("http://localhost:3001/api/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          originalPath: currentStory.path,
          content: data,
          version: version
        })
      });

      const result = await response.json();
      if (response.ok) {
        setLastAutoSave(new Date());
      } else {
        if (!silent) alert(`Failed to save: ${result.error}`);
        console.error(`Save (${version}) failed: ${result.error}`);
        if (!silent) downloadJson(`${id}_${version}.json`, data);
      }
    } catch (err) {
      console.error("Save failed, falling back to download", err);
      const suffix = version === "v2" ? "_v2" : "_v1";
      if (!silent) downloadJson(`${id}${suffix}.json`, data);
    }
  };

  // Auto-save logic
  const saveRef = useRef(handleSave);

  useEffect(() => {
    saveRef.current = handleSave;
  });

  // Discover backend port on app startup
  useEffect(() => {
    // Clear cache on mount to force re-discovery
    clearBackendCache();
    // Pre-discover backend URL (this will cache it for later use)
    getBackendUrl().catch(err => {
      console.warn("Backend port discovery failed, will use default port:", err);
    });
  }, []); // Run once on mount

  // Save culture to cache when it changes
  useEffect(() => {
    const cache = loadFolderCache();
    if (cache) {
      saveFolderCache({
        ...cache,
        culture: culture
      });
    }
  }, [culture]);

  // Keyboard shortcut: Cmd+S / Ctrl+S to save JSON
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Check for Cmd+S (Mac) or Ctrl+S (Windows/Linux)
      if ((e.metaKey || e.ctrlKey) && e.key === 's') {
        e.preventDefault(); // Prevent default browser save behavior

        // Save both v1 and v2
        if (selectedStoryIndex >= 0 && storyFiles[selectedStoryIndex]) {
          saveRef.current("v1", true); // Silent save for v1
          saveRef.current("v2", true); // Silent save for v2
        } else {
          alert("No story selected to save.");
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [selectedStoryIndex, storyFiles]);

  useEffect(() => {
    const interval = setInterval(() => {
      if (selectedStoryIndex !== -1) {
        saveRef.current("v1", true);
        saveRef.current("v2", true);
      }
    }, 5 * 60 * 1000);

    return () => clearInterval(interval);
  }, [selectedStoryIndex]);

  // Auto-save function (extracted for reuse)
  const performAutoSave = React.useCallback(() => {
    if (selectedStoryIndex === -1) {
      return;
    }
    
    const currentStory = storyFiles[selectedStoryIndex];
    if (!currentStory) {
      return;
    }

    const saveData = (version) => {
      const data = version === "v2" ? jsonV2 : jsonV1;
      const payload = JSON.stringify({
        originalPath: currentStory.path,
        content: data,
        version: version
      });

      // Use sendBeacon as primary method (designed for page unload)
      // Modern browsers block synchronous XHR during page dismissal
      if (navigator.sendBeacon) {
        try {
          // Send as plain text to avoid CORS preflight (simple request)
          // Server will parse it as JSON
          const sent = navigator.sendBeacon("http://localhost:3001/api/save", payload);
          if (sent) {
            setLastAutoSave(new Date());
          } else {
            console.warn(`Auto-save ${version} failed: sendBeacon returned false`);
          }
        } catch (beaconErr) {
          console.error(`Auto-save ${version} error:`, beaconErr);
        }
      } else {
        // Fallback: Try fetch with keepalive (if sendBeacon not available)
        try {
          fetch("http://localhost:3001/api/save", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: payload,
            keepalive: true // Allows request to continue after page unloads
          }).then(() => {
            setLastAutoSave(new Date());
          }).catch(err => {
            console.error(`Auto-save ${version} error:`, err);
          });
        } catch (fetchErr) {
          console.error(`Auto-save ${version} error:`, fetchErr);
        }
      }
    };

    // Save both versions
    saveData("v1");
    saveData("v2");
  }, [selectedStoryIndex, storyFiles, jsonV1, jsonV2]);

  // Save before page unload/refresh
  useEffect(() => {
    const handleBeforeUnload = (e) => {
      performAutoSave();
    };

    // Also listen to pagehide event as a backup (more reliable in some browsers)
    const handlePageHide = (e) => {
      // Only save if page is being unloaded (not just hidden)
      if (e.persisted === false) {
        performAutoSave();
      }
    };

    // Also use visibilitychange as additional backup
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'hidden') {
        // Only save if we're actually leaving (not just tab switching)
        // Use a small delay to check if page is really unloading
        setTimeout(() => {
          if (document.visibilityState === 'hidden') {
            performAutoSave();
          }
        }, 100);
      }
    };

    window.addEventListener("beforeunload", handleBeforeUnload);
    window.addEventListener("pagehide", handlePageHide);
    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
      window.removeEventListener("pagehide", handlePageHide);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [performAutoSave]);

  // Track all highlighted narratives' time orders and positions
  const [highlightedNarrativePositions, setHighlightedNarrativePositions] = useState([]); // Array of { key, top, order }

  // Scroll to summary focus
  useEffect(() => {
    const focusHighlight = highlightedRanges["summary-focus"];
    if (focusHighlight) {
      setTimeout(() => {
        const el = document.getElementById("summary-focus-mark");
        if (el) {
          el.scrollIntoView({ behavior: "smooth", block: "center" });
        }
      }, 100);
    }
  }, [highlightedRanges]);

  useEffect(() => {
    // Find all highlighted narratives
    const narrativeKeys = Object.keys(highlightedRanges).filter(key =>
      key.startsWith("narrative-") && highlightedRanges[key]
    );

    if (narrativeKeys.length === 0) {
      setHighlightedNarrativePositions([]);
      return;
    }

    setTimeout(() => {
      const positions = [];

      narrativeKeys.forEach(narrativeKey => {
        const highlightedRange = highlightedRanges[narrativeKey];

        // Find the narrative in narrativeStructure by matching text span
        const narrative = narrativeStructure.find(n =>
          typeof n === "object" &&
          n.text_span &&
          n.text_span.start === highlightedRange.start &&
          n.text_span.end === highlightedRange.end
        );

        if (narrative && narrative.time_order != null) {
          const markId = `${narrativeKey}-mark`;
          const markEl = document.getElementById(markId);
          if (markEl) {
            const textDisplay = markEl.closest(".story-text-display");
            if (textDisplay) {
              const markRect = markEl.getBoundingClientRect();
              const textDisplayRect = textDisplay.getBoundingClientRect();

              // Position relative to textDisplay
              const relativeTop = markRect.top - textDisplayRect.top + textDisplay.scrollTop;

              positions.push({
                key: narrativeKey,
                top: relativeTop,
                order: narrative.time_order
              });
            }
          }
        }
      });

      setHighlightedNarrativePositions(positions);
    }, 150);
  }, [highlightedRanges, narrativeStructure]);

  // Update position on scroll
  useEffect(() => {
    const textDisplay = document.querySelector(".story-text-display");
    if (!textDisplay) return;

    const handleScroll = () => {
      // Find all highlighted narratives
      const narrativeKeys = Object.keys(highlightedRanges).filter(key =>
        key.startsWith("narrative-") && highlightedRanges[key]
      );

      if (narrativeKeys.length === 0) {
        setHighlightedNarrativePositions([]);
        return;
      }

      const positions = [];

      narrativeKeys.forEach(narrativeKey => {
        const highlightedRange = highlightedRanges[narrativeKey];

        const narrative = narrativeStructure.find(n =>
          typeof n === "object" &&
          n.text_span &&
          n.text_span.start === highlightedRange.start &&
          n.text_span.end === highlightedRange.end
        );

        if (narrative && narrative.time_order != null) {
          const markId = `${narrativeKey}-mark`;
          const markEl = document.getElementById(markId);
          if (markEl && textDisplay) {
            const markRect = markEl.getBoundingClientRect();
            const textDisplayRect = textDisplay.getBoundingClientRect();

            const relativeTop = markRect.top - textDisplayRect.top + textDisplay.scrollTop;

            positions.push({
              key: narrativeKey,
              top: relativeTop,
              order: narrative.time_order
            });
          }
        }
      });

      setHighlightedNarrativePositions(positions);
    };

    textDisplay.addEventListener("scroll", handleScroll);
    return () => textDisplay.removeEventListener("scroll", handleScroll);
  }, [highlightedRanges, narrativeStructure]);

  const loadState = (loaded) => {
    if (loaded.id) {
      setId(loaded.id);
      // Extract title from ID if not explicitly provided
      const extractedTitle = extractTitleFromId(loaded.id);
      if (extractedTitle) {
        setTitle(extractedTitle);
      } else if (loaded.title) {
        setTitle(loaded.title);
      }
    }
    if (loaded.culture) setCulture(loaded.culture);

    setMeta(prev => ({ ...prev, ...loaded.meta }));
    if (loaded.sourceText) {
      setSourceText(loaded.sourceText);
    }
    setMotif(prev => {
      const loadedMotif = { ...loaded.motif };
      // Migrate motif_type from string to array if needed
      if (loadedMotif.motif_type !== undefined) {
        if (typeof loadedMotif.motif_type === "string") {
          loadedMotif.motif_type = loadedMotif.motif_type ? [loadedMotif.motif_type] : [];
        } else if (!Array.isArray(loadedMotif.motif_type)) {
          loadedMotif.motif_type = [];
        }
      }
      // Ensure atu_categories is an array
      if (loadedMotif.atu_categories !== undefined) {
        if (typeof loadedMotif.atu_categories === "string") {
          loadedMotif.atu_categories = loadedMotif.atu_categories
            ? [loadedMotif.atu_categories]
            : [];
        } else if (!Array.isArray(loadedMotif.atu_categories)) {
          loadedMotif.atu_categories = [];
        }
      }
      return { ...prev, ...loadedMotif };
    });
    
    if (loaded.paragraphSummaries) {
      if (Array.isArray(loaded.paragraphSummaries)) {
        // Legacy format no longer supported for segmented summaries.
        setParagraphSummaries({ perSection: {}, combined: [], whole: "" });
      } else if (typeof loaded.paragraphSummaries === "object") {
        const combined = Array.isArray(loaded.paragraphSummaries.combined)
          ? loaded.paragraphSummaries.combined.filter(c => c && c.start_section && c.end_section)
          : [];
        setParagraphSummaries({
          perSection: loaded.paragraphSummaries.perSection || {},
          combined,
          whole: loaded.paragraphSummaries.whole || ""
        });
      }
    }
    if (loaded.proppFns) setProppFns(loaded.proppFns);
    if (loaded.proppNotes) setProppNotes(loaded.proppNotes);
    if (loaded.narrativeStructure) setNarrativeStructure(loaded.narrativeStructure);
    if (loaded.crossValidation) setCrossValidation(prev => ({ ...prev, ...loaded.crossValidation }));
    if (loaded.qa) setQa(prev => ({ ...prev, ...loaded.qa }));
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
      atu_categories: [],
      motif_type: [],
      character_archetypes: [],
      obstacle_pattern: [],
      obstacle_thrower: [],
      helper_type: [],
      thinking_process: "",
      atu_evidence: {},
      motif_evidence: {}
    });
    setParagraphSummaries({ perSection: {}, combined: [], whole: "" });
    setProppFns([emptyProppFn()]);
    setProppNotes("");
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

  // ========== File Handling ==========
  const loadFilesFromFolderSelection = async (filesLike, folderPathHint = null) => {
    const files = filesLike;
    if (!files || files.length === 0) return;

    // If there's already loaded data, save it before loading new folder
    if (selectedStoryIndex >= 0 && storyFiles[selectedStoryIndex]) {
      try {
        await handleSave("v1", true); // Silent save for v1
        await handleSave("v2", true); // Silent save for v2
      } catch (err) {
        console.error("Failed to save before opening new folder:", err);
        // Continue loading new folder even if save fails
      }
    }

    const { texts, v1Jsons, v2Jsons } = organizeFiles(files);
    texts.sort((a, b) => a.id.localeCompare(b.id, undefined, { numeric: true, sensitivity: 'base' }));

    const withContent = await Promise.all(
      texts.map(async (t) => {
        const textRaw = await t.file.text();
        const text = textRaw.replace(/\r\n/g, '\n');
        return { ...t, name: t.file.name, text };
      })
    );

    setStoryFiles(withContent);
    setV1JsonFiles(v1Jsons);
    setV2JsonFiles(v2Jsons);

    // Extract folder path and save to cache
    const folderPath = extractFolderPath(files, folderPathHint);
    const cache = loadFolderCache();
    const targetIndex = (cache && cache.folderPath === folderPath && cache.selectedIndex >= 0 && cache.selectedIndex < withContent.length)
      ? cache.selectedIndex
      : 0;

    // Save folder cache
    saveFolderCache({
      folderPath: folderPath,
      selectedIndex: targetIndex,
      culture: culture
    });

    if (withContent.length > 0) {
      selectStoryWithData(targetIndex, withContent, v1Jsons, v2Jsons);
    }
  };

  const handleStoryFilesChange = async (event) => {
    const files = event.target.files;
    if (!files) return;
    await loadFilesFromFolderSelection(files);
  };

  const handlePickDirectory = async (files, folderName) => {
    await loadFilesFromFolderSelection(files, folderName);
  };

  const selectStoryWithData = async (index, texts, v1Map, v2Map) => {
    setSelectedStoryIndex(index);
    const story = texts[index];
    if (!story) return;

    const idGuess = story.id;
    setId(idGuess);
    // Extract title from ID (everything after second underscore)
    const extractedTitle = extractTitleFromId(idGuess);
    setTitle(extractedTitle || "");
    // Extract path starting from datasets directory
    let datasetPath = relPathToDatasetHint(story.path);
    // Ensure it starts with "datasets/" or extract from full path
    if (!datasetPath.startsWith("datasets/")) {
      // Try to find datasets in the path
      const datasetsIndex = datasetPath.indexOf("datasets/");
      if (datasetsIndex !== -1) {
        datasetPath = datasetPath.substring(datasetsIndex);
      } else {
        // If datasets not found, prepend it (assuming structure)
        datasetPath = `datasets/${datasetPath}`;
      }
    }

    setSourceText((prev) => ({
      ...prev,
      text: story.text,
      reference_uri: datasetPath
    }));

    resetState();
    setHighlightedRanges({});
    setHighlightedChars({});

    try {
      const response = await fetch("http://localhost:3001/api/load", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ originalPath: story.path })
      });
      
      const result = await response.json();
      if (result.found && result.content) {
        const mappedState = result.version === 2 ? mapV2ToState(result.content) : mapV1ToState(result.content);
        loadState(mappedState);
        return;
      }
    } catch (err) {
      console.warn("Server load failed, falling back to browser memory files", err);
    }

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
    // Update cache with new selected index
    const cache = loadFolderCache();
    if (cache) {
      saveFolderCache({
        ...cache,
        selectedIndex: index
      });
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

    const preRange = range.cloneRange();
    preRange.selectNodeContents(container);
    preRange.setEnd(range.startContainer, range.startOffset);
    const start = preRange.toString().length;
    const end = start + range.toString().length;
    const text = range.toString();

    setCurrentSelection({ start, end, text });
  };

  // ========== Context Menu Handlers ==========
  const handleContextMenu = (e) => {
    // Check if there's a text selection
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed || !selection.toString().trim()) {
      return; // Don't show menu if no text is selected
    }

    // Verify selection is within the story content
    const container = document.getElementById("story-content-pre");
    if (!container || !container.contains(selection.rangeCount > 0 ? selection.getRangeAt(0).commonAncestorContainer : null)) {
      return;
    }

    // Update currentSelection if needed (in case user right-clicked without mouseup)
    const range = selection.getRangeAt(0);
    if (container && container.contains(range.commonAncestorContainer)) {
      const preRange = range.cloneRange();
      preRange.selectNodeContents(container);
      preRange.setEnd(range.startContainer, range.startOffset);
      const start = preRange.toString().length;
      const end = start + range.toString().length;
      const text = range.toString();
      setCurrentSelection({ start, end, text });
    }

    e.preventDefault();
    setContextMenu({
      visible: true,
      x: e.clientX,
      y: e.clientY
    });
  };

  const closeContextMenu = () => {
    setContextMenu({ visible: false, x: 0, y: 0 });
  };

  // Close context menu when clicking outside or pressing Escape
  useEffect(() => {
    const handleClickOutside = () => {
      if (contextMenu.visible) {
        closeContextMenu();
      }
    };

    const handleEscape = (e) => {
      if (e.key === 'Escape' && contextMenu.visible) {
        closeContextMenu();
      }
    };

    if (contextMenu.visible) {
      document.addEventListener('click', handleClickOutside);
      document.addEventListener('keydown', handleEscape);
      return () => {
        document.removeEventListener('click', handleClickOutside);
        document.removeEventListener('keydown', handleEscape);
      };
    }
  }, [contextMenu.visible]);

  const handleCreateCharacter = () => {
    if (!currentSelection) return;

    // Extract a name from the selected text (first word or first few words)
    const selectedText = currentSelection.text.trim();
    const nameGuess = selectedText.split(/\s+/)[0].substring(0, 30); // First word, max 30 chars

    // Calculate the index of the new character (will be the last one)
    const currentCharacters = Array.isArray(motif.character_archetypes) 
      ? motif.character_archetypes 
      : [];
    const newIndex = currentCharacters.length;

    // Add new character
    setMotif(prev => ({
      ...prev,
      character_archetypes: [
        ...prev.character_archetypes,
        {
          name: nameGuess,
          alias: "",
          archetype: ""
        }
      ]
    }));

    // Set the newly created character index for auto-focus
    setNewlyCreatedCharacterIndex(newIndex);

    // Navigate to characters tab
    setActiveTab("characters");
  };

  const handleCreateNarrative = () => {
    if (!currentSelection) return;

    // Calculate next time_order
    const maxTimeOrder = Math.max(
      0,
      ...narrativeStructure
        .filter(n => typeof n === "object" && n.time_order != null)
        .map(n => n.time_order || 0)
    );

    // Create new narrative event with the selected text span
    const newEvent = {
      id: generateUUID(),
      event_type: "",
      description: currentSelection.text.trim().substring(0, 100), // Preview
      agents: [],
      targets: [],
      text_span: {
        start: currentSelection.start,
        end: currentSelection.end,
        text: currentSelection.text
      },
      target_type: "character",
      object_type: "",
      instrument: "",
      time_order: maxTimeOrder + 1
    };

    setNarrativeStructure(prev => [...prev, newEvent]);

    // Navigate to narrative tab
    setActiveTab("narrative");
  };

  const handleCreatePropp = () => {
    if (!currentSelection) return;

    // Create new Propp function with the selected text span
    const newPropp = {
      id: generateUUID(),
      fn: "",
      spanType: "text",
      span: { start: 0, end: 0 },
      textSpan: {
        start: currentSelection.start,
        end: currentSelection.end,
        text: currentSelection.text
      },
      evidence: currentSelection.text.trim().substring(0, 100), // Preview
      narrative_event_id: null
    };

    setProppFns(prev => [...prev, newPropp]);

    // Navigate to propp tab
    setActiveTab("propp");
  };

  // ========== Propp Functions ==========
  const onAddProppFn = (newEvent) => {
    if (!newEvent.event_type || newEvent.event_type === "OTHER") return;

    setProppFns((prev) => {
      const existingIndex = prev.findIndex(p => p.narrative_event_id === newEvent.id);

      if (existingIndex >= 0) {
        const next = [...prev];
        next[existingIndex] = {
          ...next[existingIndex],
          fn: newEvent.event_type,
          textSpan: newEvent.text_span || next[existingIndex].textSpan,
          evidence: newEvent.description || next[existingIndex].evidence
        };
        return next;
      } else {
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
    const validNarratives = narrativeStructure.filter(n =>
      n.id && n.event_type && n.event_type !== "OTHER"
    );

    setProppFns(prev => {
      const next = [...prev];

      validNarratives.forEach(narrative => {
        const existingIdx = next.findIndex(p => p.narrative_event_id === narrative.id);

        if (existingIdx === -1) {
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
          const existing = next[existingIdx];
          next[existingIdx] = {
            ...existing,
            fn: narrative.event_type,
            textSpan: narrative.text_span || existing.textSpan,
            evidence: narrative.description || existing.evidence
          };
        }
      });

      return next;
    });
  };

  // ========== Render Highlights ==========
  const renderStoryText = () => {
    const text = storyFiles[selectedStoryIndex]?.text;
    if (!text) return null;

    const termMap = {};
    const allTerms = [];
    const motifChars = motif.character_archetypes || [];

    Object.entries(highlightedChars).forEach(([charName, color]) => {
      const charData = motifChars.find(c => (c.name || "").trim() === charName);
      if (!charData) return;

      const names = [charData.name];
      if (charData.alias) {
        names.push(...charData.alias.split(/;|；/).map(s => s.trim()));
      }

      names.filter(n => n).forEach(term => {
        termMap[term.toLowerCase()] = color;
        allTerms.push(term);
      });
    });

    allTerms.sort((a, b) => b.length - a.length);

    const allHighlights = [];

    if (allTerms.length > 0) {
      const escapedTerms = allTerms.map(t => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
      const regex = new RegExp(`(${escapedTerms.join("|")})`, "gi");
      let match;
      while ((match = regex.exec(text)) !== null) {
        const term = match[0];
        const start = match.index;
        const end = start + term.length;
        const color = termMap[term.toLowerCase()];
        if (color) {
          allHighlights.push({ start, end, color, priority: 1 });
        }
      }
    }

    if (highlightedRanges) {
      Object.entries(highlightedRanges).forEach(([key, r]) => {
        if (r && typeof r.start === 'number' && typeof r.end === 'number') {
          allHighlights.push({ ...r, id: key, priority: 2 });
        }
      });
    }

    if (!allHighlights.length) return text;

    allHighlights.sort((a, b) => a.start - b.start);

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

      const active = allHighlights
        .filter(h => h.start <= p1 && h.end >= p2)
        .sort((a, b) => b.priority - a.priority);

      const topHighlight = active[0];

      if (topHighlight) {
        // Set id for scrolling: summary-focus, narrative, or propp highlights
        let markId = undefined;
        if (topHighlight.id === "summary-focus") {
          markId = "summary-focus-mark";
        } else if (topHighlight.id && (topHighlight.id.startsWith("narrative-") || topHighlight.id.startsWith("propp-"))) {
          markId = `${topHighlight.id}-mark`;
        }

        segments.push(
          <mark
            key={i}
            id={markId}
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
  };

  // ========== Render ==========
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
          <StoryBrowser
            storyFiles={storyFiles}
            selectedIndex={selectedStoryIndex}
            onFilesChange={handleStoryFilesChange}
            onPickDirectory={handlePickDirectory}
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
                <div
                  className="story-text-display"
                  onMouseUp={handleStorySelection}
                  onContextMenu={handleContextMenu}
                  style={{ position: "relative", paddingLeft: "80px" }}
                >
                  {highlightedNarrativePositions.map((pos) => (
                    <div
                      key={pos.key}
                      style={{
                        position: "absolute",
                        left: "0px",
                        top: `${pos.top}px`,
                        backgroundColor: "#60a5fa",
                        color: "#fff",
                        padding: "4px 8px",
                        borderRadius: "4px",
                        fontSize: "0.75rem",
                        fontWeight: "bold",
                        zIndex: 10,
                        boxShadow: "0 2px 4px rgba(0,0,0,0.2)",
                        whiteSpace: "nowrap",
                        transition: "top 0.2s ease",
                        maxWidth: "60px",
                        textAlign: "center"
                      }}
                    >
                      #{pos.order}
                    </div>
                  ))}
                  <pre id="story-content-pre">
                    {renderStoryText()}
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
            {["characters", "narrative", "propp", "summaries", "motifs", "ending-values", "metadata", "qa"].map(tab => (
              <button
                key={tab}
                className={`tab-btn ${activeTab === tab ? "active" : ""}`}
                onClick={() => setActiveTab(tab)}
              >
                {tab.split("-").map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(" ")}
              </button>
            ))}
          </div>

          <div className="inspector-content">
            {activeTab === "characters" && (
              <CharacterSection 
                motif={motif} 
                setMotif={setMotif} 
                highlightedChars={highlightedChars}
                setHighlightedChars={setHighlightedChars}
                newlyCreatedCharacterIndex={newlyCreatedCharacterIndex}
                setNewlyCreatedCharacterIndex={setNewlyCreatedCharacterIndex}
                onAutoAnnotateCharacters={handleAutoAnnotateCharacters}
                autoAnnotateCharactersLoading={autoAnnotateCharactersLoading}
              />
            )}

            {activeTab === "narrative" && (
              <NarrativeSection
                narrativeStructure={narrativeStructure}
                setNarrativeStructure={setNarrativeStructure}
                crossValidation={crossValidation}
                setCrossValidation={setCrossValidation}
                motif={motif}
                currentSelection={currentSelection}
                onAddProppFn={onAddProppFn}
                highlightedRanges={highlightedRanges}
                setHighlightedRanges={setHighlightedRanges}
                onAutoSegmentNarratives={handleAutoSegmentNarratives}
                autoSegmentNarrativesLoading={autoSegmentNarrativesLoading}
                onAutoAnnotateEvent={handleAutoAnnotateEvent}
                autoAnnotateEventLoading={autoAnnotateEventLoading}
              />
            )}

            {activeTab === "propp" && (
              <ProppSection
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
                sourceLanguage={sourceText.language}
                narrativeStructure={narrativeStructure}
                highlightedRanges={highlightedRanges}
                setHighlightedRanges={setHighlightedRanges}
                onAutoSummarize={handleAutoSummarize}
                autoSummariesLoading={autoSummariesLoading}
                autoSummariesProgress={autoSummariesProgress}
              />
            )}

            {activeTab === "motifs" && (
              <MotifSection
                motif={motif}
                setMotif={setMotif}
                onAutoDetectMotifAtu={handleAutoDetectMotifAtu}
                autoDetectMotifLoading={autoDetectMotifLoading}
                  textSections={deriveTextSectionsFromNarratives(narrativeStructure, sourceText.text)}
                  wholeSummary={paragraphSummaries.whole || ""}
              />
            )}

            {activeTab === "ending-values" && (
              <EndingAndValuesSection
                meta={meta}
                setMeta={setMeta}
              />
            )}

            {activeTab === "metadata" && (
              <>
                <StoryMetadata
                  id={id}
                  culture={culture}
                  title={title}
                  onChangeId={handleIdChange}
                  onChangeCulture={setCulture}
                  onChangeTitle={setTitle}
                  sourceText={sourceText}
                  setSourceText={setSourceText}
                />
              </>
            )}

            {activeTab === "qa" && (
              <QASection
                qa={qa}
                setQa={setQa}
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

      <ContextMenu
        visible={contextMenu.visible}
        x={contextMenu.x}
        y={contextMenu.y}
        onClose={closeContextMenu}
        onCreateCharacter={handleCreateCharacter}
        onCreateNarrative={handleCreateNarrative}
        onCreatePropp={handleCreatePropp}
      />
    </div>
  );
}
