
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
      texts.push({ file, id: fileName.replace('.txt', ''), path });
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
      obstacle_pattern: themes.obstacle_pattern || "",
      obstacle_thrower: themes.obstacle_thrower || "",
      helper_type: themes.helper_type || "",
      thinking_process: themes.thinking_process || ""
    },
    
    // Narrative Structure
    narrativeStructure: (data.narrative_events || []).map(evt => {
      // V2 events are objects. V1 mixed strings and objects. App supports object.
      return evt;
    }),
    
    // Analysis / Deep Annotation
    proppFns: analysis.propp_functions || [],
    proppNotes: analysis.propp_notes || "",
    paragraphSummaries: analysis.paragraph_summaries || [],
    
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
    
    motif: data.annotation?.motif || {},
    
    narrativeStructure: data.narrative_structure || [],
    
    proppFns: data.annotation?.deep?.propp_functions || [],
    proppNotes: data.annotation?.deep?.propp_notes || "",
    paragraphSummaries: data.annotation?.deep?.paragraph_summaries || [],
    
    crossValidation: data.cross_validation || {},
    
    qa: data.qa || {}
  };
}

