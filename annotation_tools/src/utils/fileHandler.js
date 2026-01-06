
// Helper to organize files into categories
export function organizeFiles(fileList) {
  const texts = [];
  const v1Jsons = {};
  const v2Jsons = {};

  Array.from(fileList).forEach((file) => {
    const path = file.webkitRelativePath || file.name;
    const parts = path.split('/');
    const fileName = parts.pop();
    const dir = parts.join('/');

    if (fileName.endsWith('.txt')) {
      const id = fileName.replace('.txt', '');
      texts.push({ file, id, path });
    } else if (fileName.endsWith('.json')) {
      const id = fileName.replace(/_v[12]\.json$/, '').replace('.json', '');
      
      // Heuristic: check directory or filename suffix
      // Users might name v2 files as *_v2.json or put them in json_v2 folder
      const isV2Folder = dir.endsWith('json_v2') || dir.includes('/json_v2/');
      const isV2File = fileName.endsWith('_v2.json');
      
      // Also check content version if we could read it, but we can't here easily.
      // We rely on folder structure or naming conventions for now.
      // The user prompt said: "open or create 2 json folders... json and json_v2"
      
      if (isV2Folder || isV2File) {
        v2Jsons[id] = file;
      } else {
        v1Jsons[id] = file;
      }
    }
  });

  return { texts, v1Jsons, v2Jsons };
}

// Helper to generate UUID
export function generateUUID() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

// Helper to normalize obstacle_thrower (convert string to array for backward compatibility)
function normalizeObstacleThrower(value) {
  if (!value) return [];
  if (Array.isArray(value)) return value;
  if (typeof value === 'string' && value.trim()) return [value.trim()];
  return [];
}

// Helper to normalize helper_type (convert string to array for backward compatibility)
function normalizeHelperType(value) {
  if (!value) return [];
  if (Array.isArray(value)) return value;
  if (typeof value === 'string' && value.trim()) return [value.trim()];
  return [];
}

function normalizeEvidenceMap(value) {
  const WHOLE_SUMMARY_KEY = "__WHOLE_SUMMARY__";
  const input = (value && typeof value === "object" && !Array.isArray(value)) ? value : {};
  const out = {};
  Object.keys(input).forEach((label) => {
    const v = input[label] || {};
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
    out[label] = { evidence_keys: uniq };
  });
  return out;
}

// Helper to extract action fields from action_layer
function extractActionFieldsFromLayer(evt) {
  if (evt.action_layer) {
    return {
      action_category: evt.action_layer.category || "",
      action_type: evt.action_layer.type || "",
      action_context: evt.action_layer.context || "",
      action_status: evt.action_layer.status || ""
    };
  }
  return {
    action_category: evt.action_category || "",
    action_type: evt.action_type || "",
    action_context: evt.action_context || "",
    action_status: evt.action_status || ""
  };
}

// Helper to map V2 JSON to App State
export function mapV2ToState(data) {
  // Ensure defaults
  const meta = data.metadata || {};
  const themes = data.themes_and_motifs || {};
  const analysis = data.analysis || {};
  
  return {
    id: meta.id || "",
    culture: meta.culture || "",
    title: meta.title || "",
    annotationLevel: meta.annotation_level || "story",
    
    // Metadata Section
    meta: {
      atu_type: themes.atu_type || "",
      main_motif: themes.atu_description || "",
      ending_type: themes.ending_type || "",
      key_values: themes.key_values || []
    },
    
    // Characters -> mapped to motif.character_archetypes
    motif: {
      character_archetypes: data.characters || [],
      motif_type: (() => {
        const mt = themes.motif_type;
        if (Array.isArray(mt)) return mt;
        if (typeof mt === "string" && mt.trim()) return [mt];
        return [];
      })(),
      atu_categories: (() => {
        const ac = themes.atu_categories;
        if (Array.isArray(ac)) return ac;
        if (typeof ac === "string" && ac.trim()) return [ac];
        return [];
      })(),
      atu_evidence: (() => {
        return normalizeEvidenceMap(themes.atu_evidence);
      })(),
      motif_evidence: (() => {
        return normalizeEvidenceMap(themes.motif_evidence);
      })(),
      obstacle_pattern: themes.obstacle_pattern || "",
      obstacle_thrower: normalizeObstacleThrower(themes.obstacle_thrower),
      helper_type: normalizeHelperType(themes.helper_type),
      thinking_process: themes.thinking_process || ""
    },
    
    // Narrative Structure
    narrativeStructure: (data.narrative_events || []).map((evt, index) => {
      // V2 events are objects. V1 mixed strings and objects. App supports object.
      if (typeof evt === "string") {
        return {
          id: generateUUID(),
          event_type: "OTHER",
          description: evt,
          agents: [],
          targets: [],
          text_span: null,
          target_type: "character",
          object_type: "",
          instrument: "",
          time_order: index + 1,
          relationship_level1: "",
          relationship_level2: "",
          relationship_multi: [],
          sentiment: "",
          action_category: "",
          action_type: "",
          action_context: "",
          action_status: ""
        };
      }
      return {
        ...evt,
        // Ensure new fields exist
        id: evt.id || generateUUID(),
        target_type: evt.target_type || "character",
        object_type: evt.object_type || "",
        instrument: evt.instrument || "",
        time_order: evt.time_order ?? (index + 1),
        relationship_level1: evt.relationship_level1 || "",
        relationship_level2: evt.relationship_level2 || "",
        relationship_multi: Array.isArray(evt.relationship_multi)
          ? evt.relationship_multi
          : (evt.relationship_multi ? [evt.relationship_multi] : []),
        sentiment: evt.sentiment || "",
        ...extractActionFieldsFromLayer(evt)
      };
    }),
    
    // Analysis / Deep Annotation
    proppFns: (analysis.propp_functions || []).map(pf => ({
      ...pf,
      id: pf.id || generateUUID(),
      // Ensure narrative_event_id exists if we want to link (might be null for legacy)
      narrative_event_id: pf.narrative_event_id || null
    })),
    proppNotes: analysis.propp_notes || "",
    // Migrating paragraphSummaries to new structure
    paragraphSummaries: (() => {
      const raw = analysis.paragraph_summaries;
      // Check if already new structure
      if (raw && typeof raw === "object" && !Array.isArray(raw)) {
        const combined = Array.isArray(raw.combined)
          ? raw.combined.filter(c => c && c.start_section && c.end_section)
          : [];
        return {
          perSection: raw.per_section || {},
          combined,
          whole: raw.whole || ""
        };
      }
      // Legacy array format - migrate
      if (Array.isArray(raw)) {
        // Deprecated: old paragraph-based format
        return { perSection: {}, combined: [], whole: "" };
      }
      return { perSection: {}, combined: [], whole: "" };
    })(),
    
    // Cross Validation
    crossValidation: {
      bias_reflection: analysis.bias_reflection || {
        cultural_reading: "",
        gender_norms: "",
        hero_villain_mapping: "",
        ambiguous_motifs: []
      }
    },
    
    // QA
    qa: {
      annotator: meta.annotator || "",
      date_annotated: meta.date_annotated || new Date().toISOString().split("T")[0],
      confidence: meta.confidence || "High",
      notes: analysis.qa_notes || ""
    },

    // Source Text
    sourceText: data.source_info ? {
      text: data.source_info.text_content || "",
      language: data.source_info.language || "",
      type: data.source_info.type || "",
      reference_uri: data.source_info.reference_uri || ""
    } : {
      text: "",
      language: "",
      type: "",
      reference_uri: ""
    }
  };
}

// Helper to map V1 JSON to App State
export function mapV1ToState(data) {
  return {
    id: data.id || "",
    culture: data.culture || "",
    title: data.title || "",
    annotationLevel: data.annotation_level || "story",
    
    meta: data.metadata || {},
    
    motif: {
      ...(data.annotation?.motif || {}),
      motif_type: (() => {
        const mt = data.annotation?.motif?.motif_type;
        if (Array.isArray(mt)) return mt;
        if (typeof mt === "string" && mt.trim()) return [mt];
        return [];
      })(),
      atu_categories: (() => {
        const ac = data.annotation?.motif?.atu_categories;
        if (Array.isArray(ac)) return ac;
        if (typeof ac === "string" && ac.trim()) return [ac];
        return [];
      })(),
      atu_evidence: (() => {
        return normalizeEvidenceMap(data.annotation?.motif?.atu_evidence);
      })(),
      motif_evidence: (() => {
        return normalizeEvidenceMap(data.annotation?.motif?.motif_evidence);
      })(),
      obstacle_thrower: normalizeObstacleThrower(data.annotation?.motif?.obstacle_thrower),
      helper_type: normalizeHelperType(data.annotation?.motif?.helper_type)
    },
    
    narrativeStructure: (data.narrative_structure || []).map((evt, index) => {
      if (typeof evt === "string") {
        return {
          id: generateUUID(),
          event_type: "OTHER",
          description: evt,
          agents: [],
          targets: [],
          text_span: null,
          target_type: "character",
          object_type: "",
          instrument: "",
          time_order: index + 1,
          relationship_level1: "",
          relationship_level2: "",
          relationship_multi: [],
          sentiment: "",
          action_category: "",
          action_type: "",
          action_context: "",
          action_status: ""
        };
      }
      return {
        ...evt,
        id: evt.id || generateUUID(),
        target_type: evt.target_type || "character",
        object_type: evt.object_type || "",
        instrument: evt.instrument || "",
        time_order: evt.time_order ?? (index + 1),
        relationship_level1: evt.relationship_level1 || "",
        relationship_level2: evt.relationship_level2 || "",
        relationship_multi: Array.isArray(evt.relationship_multi)
          ? evt.relationship_multi
          : (evt.relationship_multi ? [evt.relationship_multi] : []),
        sentiment: evt.sentiment || "",
        ...extractActionFieldsFromLayer(evt)
      };
    }),

    proppFns: (data.annotation?.deep?.propp_functions || []).map(pf => ({
      ...pf,
      id: pf.id || generateUUID(),
      narrative_event_id: pf.narrative_event_id || null
    })),
    proppNotes: data.annotation?.deep?.propp_notes || "",
    // Migrating paragraphSummaries to new structure
    paragraphSummaries: (() => {
      const raw = data.annotation?.deep?.paragraph_summaries;
      // Check if already new structure
      if (raw && typeof raw === "object" && !Array.isArray(raw)) {
        const combined = Array.isArray(raw.combined)
          ? raw.combined.filter(c => c && c.start_section && c.end_section)
          : [];
        return {
          perSection: raw.per_section || {},
          combined,
          whole: raw.whole || ""
        };
      }
      // Legacy array format - migrate
      if (Array.isArray(raw)) {
        // Deprecated: old paragraph-based format
        return { perSection: {}, combined: [], whole: "" };
      }
      // Fallback: support older object shape so the app doesn't crash
      if (raw && typeof raw === "object" && raw.per_paragraph) {
        return {
          perSection: raw.per_paragraph || {},
          combined: raw.combined || [],
          whole: raw.whole || ""
        };
      }
      return { perSection: {}, combined: [], whole: "" };
    })(),
    
    crossValidation: data.cross_validation || {},
    
    qa: data.qa || {},

    sourceText: data.source_text || {
      text: "",
      language: "",
      type: "",
      reference_uri: ""
    }
  };
}

