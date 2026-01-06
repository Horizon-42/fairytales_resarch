/**
 * Pure helper logic for NarrativeSection.
 *
 * IMPORTANT: These helpers are intentionally behavior-preserving refactors.
 * They should not change UX/logic; they only make code easier to read and test.
 */

export function narrativeHighlightKey(idx) {
  return `narrative-${idx}`;
}

export function narrativeHighlightMarkIdFromKey(key) {
  return `${key}-mark`;
}

export function ensureRelationshipMultiEntryShape(entry) {
  if (!entry || typeof entry !== "object") {
    return { agent: "", target: "", relationship_level1: "", relationship_level2: "", sentiment: "" };
  }
  return {
    agent: entry.agent || "",
    target: entry.target || "",
    relationship_level1: entry.relationship_level1 || "",
    relationship_level2: entry.relationship_level2 || "",
    sentiment: entry.sentiment || ""
  };
}

export function normalizeRelationshipMulti(relationshipMulti) {
  if (!relationshipMulti) return [];
  if (Array.isArray(relationshipMulti)) return relationshipMulti.map(ensureRelationshipMultiEntryShape);
  if (typeof relationshipMulti === "object") return [ensureRelationshipMultiEntryShape(relationshipMulti)];
  return [];
}

export function isMultiRelationshipEvent(item) {
  if (!item || item.target_type !== "character") return false;
  const agents = Array.isArray(item.agents) ? item.agents : [];
  const targets = Array.isArray(item.targets) ? item.targets : [];
  return agents.length > 1 || targets.length > 1;
}

export function deriveRelationshipUiState(item) {
  const safeItem = item && typeof item === "object" ? item : {};
  const multiRel = isMultiRelationshipEvent(safeItem);
  const rmList = normalizeRelationshipMulti(safeItem.relationship_multi);
  const agents = Array.isArray(safeItem.agents) ? safeItem.agents : [];
  const targets = Array.isArray(safeItem.targets) ? safeItem.targets : [];
  const { relationship_level1: effectiveRelationshipLevel1, relationship_level2: effectiveRelationshipLevel2 } =
    getEffectiveRelationshipLevels({ item: safeItem, rmList, multiRel });

  return {
    multiRel,
    rmList,
    agents,
    targets,
    effectiveRelationshipLevel1,
    effectiveRelationshipLevel2
  };
}

/**
 * Determine the relationship L1/L2 values used for the legacy (single) relationship controls.
 *
 * Behavior-preserving:
 * - In multi-person case, prefer the first relationship_multi row if present, falling back to legacy fields.
 * - Otherwise, use legacy fields.
 */
export function getEffectiveRelationshipLevels({ item, rmList, multiRel }) {
  const safeItem = item && typeof item === "object" ? item : {};
  const safeRmList = Array.isArray(rmList) ? rmList.map(ensureRelationshipMultiEntryShape) : [];

  const relationship_level1 = multiRel
    ? ((safeRmList[0] && safeRmList[0].relationship_level1) || safeItem.relationship_level1 || "")
    : (safeItem.relationship_level1 || "");

  const relationship_level2 = multiRel
    ? ((safeRmList[0] && safeRmList[0].relationship_level2) || safeItem.relationship_level2 || "")
    : (safeItem.relationship_level2 || "");

  return { relationship_level1, relationship_level2 };
}

/**
 * Ensure there is at least one relationship row when rendering multi relationship UI.
 *
 * Behavior-preserving:
 * - If relationship_multi already has entries, return them.
 * - Otherwise, create one row that (optionally) auto-fills agent/target when there is exactly one.
 * - Seeds relationship/sentiment from legacy single fields.
 */
export function ensureAtLeastOneRelationshipMulti({ item, rmList, agents, targets }) {
  const safeItem = item && typeof item === "object" ? item : {};
  const safeRmList = Array.isArray(rmList) ? rmList.map(ensureRelationshipMultiEntryShape) : [];
  if (safeRmList.length > 0) return safeRmList;

  const safeAgents = Array.isArray(agents) ? agents.filter(Boolean) : [];
  const safeTargets = Array.isArray(targets) ? targets.filter(Boolean) : [];

  const fallback = {
    agent: safeAgents.length === 1 ? safeAgents[0] : (safeAgents[0] || ""),
    target: safeTargets.length === 1 ? safeTargets[0] : (safeTargets[0] || ""),
    relationship_level1: safeItem.relationship_level1 || "",
    relationship_level2: safeItem.relationship_level2 || "",
    sentiment: safeItem.sentiment || ""
  };

  return [ensureRelationshipMultiEntryShape(fallback)];
}

export function updateRelationshipMultiRow(list, relIdx, partial, resetLevel2 = false) {
  const current = Array.isArray(list) ? list.map(ensureRelationshipMultiEntryShape) : [];
  return current.map((r, i) => {
    if (i !== relIdx) return r;
    const merged = { ...r, ...(partial || {}) };
    if (resetLevel2) merged.relationship_level2 = "";
    return ensureRelationshipMultiEntryShape(merged);
  });
}

export function addRelationshipMultiRow(list, { agents, targets }) {
  const current = Array.isArray(list) ? list.map(ensureRelationshipMultiEntryShape) : [];
  const safeAgents = Array.isArray(agents) ? agents.filter(Boolean) : [];
  const safeTargets = Array.isArray(targets) ? targets.filter(Boolean) : [];
  return [
    ...current,
    ensureRelationshipMultiEntryShape({
      agent: safeAgents.length === 1 ? safeAgents[0] : "",
      target: safeTargets.length === 1 ? safeTargets[0] : ""
    })
  ];
}

export function removeRelationshipMultiRow(list, relIdx) {
  const current = Array.isArray(list) ? list.map(ensureRelationshipMultiEntryShape) : [];
  const next = current.filter((_, i) => i !== relIdx);
  return next.length > 0 ? next : [ensureRelationshipMultiEntryShape({})];
}

export function buildSetRelationshipMultiUpdates(nextList) {
  return {
    relationship_multi: Array.isArray(nextList) ? nextList : (nextList ? [nextList] : []),
    // keep legacy fields empty for multi-person relationship
    relationship_level1: "",
    relationship_level2: "",
    // sentiment becomes per-relationship in multi-person case
    sentiment: ""
  };
}

export function formatRelationshipLevel1Label(level1) {
  if (!level1) return level1;
  const match = String(level1).match(/\(([^)]+)\)/);
  return match ? match[1] : level1;
}

/**
 * Build an updates object for a change to `agents` or `targets`.
 *
 * Mirrors the existing NarrativeSection behavior:
 * - Always sets the edited field to `values`.
 * - If relationship_multi exists, keep each relationship row's endpoints valid when
 *   an agent/target is removed (so disabled selectors don't render as '-').
 * - If the event remains multi-person / multi-relationship, clear legacy single-rel fields.
 */
export function buildMultiCharUpdatesWithEndpointSync({ item, field, values }) {
  const updates = { [field]: values };

  if (
    !item ||
    item.target_type !== "character" ||
    (field !== "agents" && field !== "targets")
  ) {
    return updates;
  }

  const currentRelList = normalizeRelationshipMulti(item.relationship_multi);
  if (currentRelList.length === 0) return updates;

  const nextAgents = field === "agents"
    ? values
    : (Array.isArray(item.agents) ? item.agents.filter(Boolean) : []);
  const nextTargets = field === "targets"
    ? values
    : (Array.isArray(item.targets) ? item.targets.filter(Boolean) : []);

  const lastAgent = nextAgents.length > 0 ? nextAgents[nextAgents.length - 1] : "";
  const lastTarget = nextTargets.length > 0 ? nextTargets[nextTargets.length - 1] : "";

  const nextRelList = currentRelList.map((r) => {
    const rr = ensureRelationshipMultiEntryShape(r);
    const next = { ...rr };

    if (field === "agents") {
      if (nextAgents.length === 1) next.agent = nextAgents[0] || "";
      else if (next.agent && !nextAgents.includes(next.agent)) next.agent = lastAgent;
      else if (!next.agent && nextAgents.length === 1) next.agent = nextAgents[0] || "";
    }

    if (field === "targets") {
      if (nextTargets.length === 1) next.target = nextTargets[0] || "";
      else if (next.target && !nextTargets.includes(next.target)) next.target = lastTarget;
      else if (!next.target && nextTargets.length === 1) next.target = nextTargets[0] || "";
    }

    return next;
  });

  updates.relationship_multi = nextRelList;

  const shouldBeMulti = (
    nextAgents.length > 1 ||
    nextTargets.length > 1 ||
    nextRelList.length > 1
  );

  if (shouldBeMulti) {
    updates.relationship_level1 = "";
    updates.relationship_level2 = "";
    updates.sentiment = "";
  }

  return updates;
}

export function computeMaxTimeOrder(narrativeStructure) {
  const list = Array.isArray(narrativeStructure) ? narrativeStructure : [];
  return Math.max(
    0,
    ...list
      .filter((n) => typeof n === "object" && n && n.time_order != null)
      .map((n) => n.time_order || 0)
  );
}

function normalizeRelationshipMultiField(relationshipMulti) {
  return Array.isArray(relationshipMulti)
    ? relationshipMulti
    : (relationshipMulti ? [relationshipMulti] : []);
}

/**
 * Build the `items` array from `narrativeStructure` exactly like NarrativeSection.
 *
 * Notes (intentional behavior preservation):
 * - Strings are converted to objects with default fields and `event_type: OTHER`.
 * - Objects missing `id` get a generated id and also get action_layer -> flat action fields compatibility.
 * - Objects with an `id` do NOT get action_layer compat mapping (kept as-is).
 */
export function buildNarrativeItems({ narrativeStructure, maxTimeOrder, uuidFn }) {
  const list = Array.isArray(narrativeStructure) ? narrativeStructure : [];
  const safeMax = typeof maxTimeOrder === "number" && Number.isFinite(maxTimeOrder) ? maxTimeOrder : computeMaxTimeOrder(list);
  const makeId = typeof uuidFn === "function" ? uuidFn : (() => "");

  return list.map((item, index) => {
    if (typeof item === "string") {
      return {
        id: makeId(),
        event_type: "OTHER",
        description: item,
        narrative_function: "",
        agents: [],
        targets: [],
        text_span: null,
        target_type: "character",
        object_type: "",
        instrument: "",
        time_order: safeMax + 1 + index,
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

    if (!item || typeof item !== "object") return item;

    if (!item.id) {
      return {
        ...item,
        id: makeId(),
        time_order: item.time_order ?? (safeMax + 1 + index),
        narrative_function: item.narrative_function || "",
        relationship_level1: item.relationship_level1 || "",
        relationship_level2: item.relationship_level2 || "",
        relationship_multi: normalizeRelationshipMultiField(item.relationship_multi),
        sentiment: item.sentiment || "",
        action_category: item.action_category || (item.action_layer?.category || ""),
        action_type: item.action_type || (item.action_layer?.type || ""),
        action_context: item.action_context || (item.action_layer?.context || ""),
        action_status: item.action_status || (item.action_layer?.status || "")
      };
    }

    return {
      ...item,
      time_order: item.time_order ?? (safeMax + 1 + index),
      narrative_function: item.narrative_function || "",
      relationship_level1: item.relationship_level1 || "",
      relationship_level2: item.relationship_level2 || "",
      relationship_multi: normalizeRelationshipMultiField(item.relationship_multi),
      sentiment: item.sentiment || ""
    };
  });
}

export function sortNarrativeItemsInPlace(items, sortByTimeOrder) {
  if (!Array.isArray(items)) return items;

  if (sortByTimeOrder) {
    items.sort((a, b) => {
      const orderA = a?.time_order ?? Infinity;
      const orderB = b?.time_order ?? Infinity;
      return orderA - orderB;
    });
    return items;
  }

  items.sort((a, b) => {
    const startA = a?.text_span?.start ?? Infinity;
    const startB = b?.text_span?.start ?? Infinity;
    return startA - startB;
  });
  return items;
}

/**
 * Find the index of an event object in the original `narrativeStructure` by its `id`.
 * Behavior-preserving: matches NarrativeSection's predicate (only objects are considered).
 */
export function findOriginalNarrativeIndexById(narrativeStructure, id) {
  const list = Array.isArray(narrativeStructure) ? narrativeStructure : [];
  return list.findIndex((n) => typeof n === "object" && n && n.id === id);
}

/**
 * Remove a single event object from `narrativeStructure` by its `id`.
 * Behavior-preserving: only removes when `typeof n === 'object'` and `n.id` matches.
 */
export function removeNarrativeEntryById(narrativeStructure, id) {
  const list = Array.isArray(narrativeStructure) ? narrativeStructure : [];
  return list.filter((n) => {
    if (typeof n === "object" && n && n.id === id) return false;
    return true;
  });
}

/**
 * Convert a string entry (legacy narrativeStructure element) into an event object.
 *
 * Behavior-preserving: matches the exact fields used in NarrativeSection's updateItem fallback.
 */
export function buildNarrativeObjectFromString({
  description,
  updates,
  uuidFn,
  timeOrder
}) {
  const makeId = typeof uuidFn === "function" ? uuidFn : (() => "");
  const safeUpdates = updates && typeof updates === "object" ? updates : {};

  return {
    id: makeId(),
    event_type: "OTHER",
    description,
    agents: [],
    targets: [],
    text_span: null,
    target_type: "character",
    object_type: "",
    instrument: "",
    time_order: timeOrder,
    relationship_level1: "",
    relationship_level2: "",
    relationship_multi: [],
    sentiment: "",
    ...safeUpdates
  };
}

/**
 * Apply an update to a narrative item by *sorted* index.
 *
 * Mirrors NarrativeSection.updateItem behavior:
 * - If the sorted item has no id, update the sorted `items` array and use that as next narrativeStructure.
 * - Otherwise, try to find the original entry in `narrativeStructure` by id.
 *   - If not found, update the sorted `items` array and use that.
 *   - If found:
 *     - If original entry is an object, shallow-merge updates.
 *     - If original entry is a string, convert it to an object with defaults and apply updates.
 */
export function applyNarrativeItemUpdate({
  items,
  narrativeStructure,
  index,
  updates,
  uuidFn,
  maxTimeOrder
}) {
  const safeItems = Array.isArray(items) ? items : [];
  const safeNarrativeStructure = Array.isArray(narrativeStructure) ? narrativeStructure : [];
  const safeUpdates = updates && typeof updates === "object" ? updates : {};

  const itemToUpdate = safeItems[index];
  if (!itemToUpdate || !itemToUpdate.id) {
    const next = [...safeItems];
    next[index] = { ...next[index], ...safeUpdates };
    return next;
  }

  const originalIndex = findOriginalNarrativeIndexById(safeNarrativeStructure, itemToUpdate.id);
  if (originalIndex === -1) {
    const next = [...safeItems];
    next[index] = { ...next[index], ...safeUpdates };
    return next;
  }

  const next = [...safeNarrativeStructure];
  if (typeof next[originalIndex] === "object" && next[originalIndex]) {
    next[originalIndex] = { ...next[originalIndex], ...safeUpdates };
    return next;
  }

  next[originalIndex] = buildNarrativeObjectFromString({
    description: next[originalIndex],
    updates: safeUpdates,
    uuidFn,
    timeOrder: maxTimeOrder + 1
  });
  return next;
}

export function toggleNarrativeHighlightMap(prev, { idx, span, color = "#60a5fa" }) {
  const next = { ...(prev || {}) };
  const key = narrativeHighlightKey(idx);
  const isAdding = !next[key];

  if (next[key]) {
    delete next[key];
    return { next, isAdding: false, key };
  }

  if (!span) return { next, isAdding: false, key };

  next[key] = {
    start: span.start,
    end: span.end,
    color
  };
  return { next, isAdding: true, key };
}

export function toggleAllNarrativeHighlightsMap(prev, { items, allHighlighted, color = "#60a5fa" }) {
  const next = { ...(prev || {}) };
  const list = Array.isArray(items) ? items : [];

  if (allHighlighted) {
    list.forEach((_, idx) => {
      const key = narrativeHighlightKey(idx);
      delete next[key];
    });
    return next;
  }

  list.forEach((item, idx) => {
    if (item && item.text_span) {
      const key = narrativeHighlightKey(idx);
      next[key] = {
        start: item.text_span.start,
        end: item.text_span.end,
        color
      };
    }
  });

  return next;
}

/**
 * Compute whether "all" narrative highlights are currently active.
 *
 * Behavior-preserving: this intentionally matches NarrativeSection's current logic,
 * including the fact that it keys by the index within the filtered `itemsWithSpan` array.
 */
export function computeAllNarrativeHighlighted({ highlightedRanges, items }) {
  if (!highlightedRanges) return false;
  const list = Array.isArray(items) ? items : [];
  const itemsWithSpan = list.filter((item) => item && item.text_span);
  if (itemsWithSpan.length === 0) return false;

  return itemsWithSpan.every((_, idx) => {
    const key = narrativeHighlightKey(idx);
    return highlightedRanges[key];
  });
}
