import { describe, expect, it } from "vitest";
import {
  buildMultiCharUpdatesWithEndpointSync,
  normalizeRelationshipMulti,
  ensureRelationshipMultiEntryShape,
  getEffectiveRelationshipLevels,
  ensureAtLeastOneRelationshipMulti,
  computeMaxTimeOrder,
  buildNarrativeItems,
  sortNarrativeItemsInPlace,
  findOriginalNarrativeIndexById,
  removeNarrativeEntryById,
  buildNarrativeObjectFromString,
  applyNarrativeItemUpdate,
  toggleNarrativeHighlightMap,
  toggleAllNarrativeHighlightsMap,
  computeAllNarrativeHighlighted,
  narrativeHighlightKey,
  narrativeHighlightMarkIdFromKey,
  updateRelationshipMultiRow,
  addRelationshipMultiRow,
  removeRelationshipMultiRow,
  deriveRelationshipUiState,
  buildSetRelationshipMultiUpdates,
} from "../../components/narrativeSectionLogic.js";

describe("narrativeSectionLogic", () => {
  it("normalizeRelationshipMulti() always returns shaped entries", () => {
    expect(normalizeRelationshipMulti(null)).toEqual([]);
    expect(normalizeRelationshipMulti({ agent: "A" })[0]).toEqual(
      ensureRelationshipMultiEntryShape({ agent: "A" })
    );
  });

  it("syncs relationship targets when targets shrink to one (bug regression)", () => {
    const item = {
      target_type: "character",
      agents: ["X"],
      targets: ["A", "B"],
      relationship_multi: [
        { agent: "X", target: "A", relationship_level1: "", relationship_level2: "", sentiment: "" }
      ]
    };

    const updates = buildMultiCharUpdatesWithEndpointSync({
      item,
      field: "targets",
      values: ["B"]
    });

    expect(updates.targets).toEqual(["B"]);
    expect(updates.relationship_multi).toHaveLength(1);
    expect(updates.relationship_multi[0].target).toBe("B");
  });

  it("syncs relationship targets when a selected target is removed (multiple remain)", () => {
    const item = {
      target_type: "character",
      agents: ["X"],
      targets: ["A", "B", "C"],
      relationship_multi: [
        { agent: "X", target: "A", relationship_level1: "", relationship_level2: "", sentiment: "" }
      ]
    };

    const updates = buildMultiCharUpdatesWithEndpointSync({
      item,
      field: "targets",
      values: ["B", "C"]
    });

    // last remaining target becomes the fallback
    expect(updates.relationship_multi[0].target).toBe("C");
  });

  it("syncs relationship agents when agents shrink to one", () => {
    const item = {
      target_type: "character",
      agents: ["X", "Y"],
      targets: ["T"],
      relationship_multi: [
        { agent: "X", target: "T", relationship_level1: "", relationship_level2: "", sentiment: "" }
      ]
    };

    const updates = buildMultiCharUpdatesWithEndpointSync({
      item,
      field: "agents",
      values: ["Y"]
    });

    expect(updates.relationship_multi[0].agent).toBe("Y");
  });

  it("clears legacy relationship fields when the event remains multi", () => {
    const item = {
      target_type: "character",
      agents: ["A", "B"],
      targets: ["T"],
      relationship_multi: [
        { agent: "A", target: "T", relationship_level1: "X", relationship_level2: "Y", sentiment: "positive" }
      ],
      relationship_level1: "SHOULD_CLEAR",
      relationship_level2: "SHOULD_CLEAR",
      sentiment: "SHOULD_CLEAR"
    };

    const updates = buildMultiCharUpdatesWithEndpointSync({
      item,
      field: "targets",
      values: ["T"]
    });

    expect(updates.relationship_level1).toBe("");
    expect(updates.relationship_level2).toBe("");
    expect(updates.sentiment).toBe("");
  });

  it("does not add relationship_multi updates when none exist", () => {
    const item = {
      target_type: "character",
      agents: ["A"],
      targets: ["T"],
      relationship_multi: []
    };

    const updates = buildMultiCharUpdatesWithEndpointSync({
      item,
      field: "targets",
      values: ["T"]
    });

    expect(updates).toEqual({ targets: ["T"] });
  });

  it("ensureAtLeastOneRelationshipMulti() falls back to legacy fields", () => {
    const item = {
      relationship_level1: "亲属关系(Family)",
      relationship_level2: "parent",
      sentiment: "positive"
    };
    const list = ensureAtLeastOneRelationshipMulti({
      item,
      rmList: [],
      agents: ["A"],
      targets: ["B"]
    });

    expect(list).toHaveLength(1);
    expect(list[0]).toEqual({
      agent: "A",
      target: "B",
      relationship_level1: "亲属关系(Family)",
      relationship_level2: "parent",
      sentiment: "positive"
    });
  });

  it("getEffectiveRelationshipLevels() prefers first relationship_multi entry in multi case", () => {
    const item = {
      relationship_level1: "LEGACY_L1",
      relationship_level2: "LEGACY_L2"
    };

    const multi = getEffectiveRelationshipLevels({
      item,
      rmList: [{ relationship_level1: "ROW_L1", relationship_level2: "ROW_L2" }],
      multiRel: true
    });
    expect(multi.relationship_level1).toBe("ROW_L1");
    expect(multi.relationship_level2).toBe("ROW_L2");

    const single = getEffectiveRelationshipLevels({
      item,
      rmList: [{ relationship_level1: "ROW_L1", relationship_level2: "ROW_L2" }],
      multiRel: false
    });
    expect(single.relationship_level1).toBe("LEGACY_L1");
    expect(single.relationship_level2).toBe("LEGACY_L2");
  });

  it("computeMaxTimeOrder() ignores non-objects and null time_order", () => {
    expect(computeMaxTimeOrder([])).toBe(0);
    expect(computeMaxTimeOrder(["x", { time_order: null }, { time_order: 3 }])).toBe(3);
  });

  it("buildNarrativeItems() converts strings and assigns time_order from maxTimeOrder", () => {
    const ids = ["id1", "id2"]; 
    const uuidFn = () => ids.shift();

    const items = buildNarrativeItems({
      narrativeStructure: ["hello", "world"],
      maxTimeOrder: 10,
      uuidFn
    });

    expect(items[0].id).toBe("id1");
    expect(items[0].event_type).toBe("OTHER");
    expect(items[0].description).toBe("hello");
    expect(items[0].time_order).toBe(11);

    expect(items[1].id).toBe("id2");
    expect(items[1].description).toBe("world");
    expect(items[1].time_order).toBe(12);
  });

  it("buildNarrativeItems() maps action_layer compat only when id is missing", () => {
    const uuidFn = () => "newid";

    const noId = buildNarrativeItems({
      narrativeStructure: [{ action_layer: { category: "C", type: "T", context: "X", status: "S" } }],
      maxTimeOrder: 0,
      uuidFn
    })[0];

    expect(noId.id).toBe("newid");
    expect(noId.action_category).toBe("C");
    expect(noId.action_type).toBe("T");
    expect(noId.action_context).toBe("X");
    expect(noId.action_status).toBe("S");

    const withId = buildNarrativeItems({
      narrativeStructure: [{ id: "keep", action_layer: { category: "C" } }],
      maxTimeOrder: 0,
      uuidFn
    })[0];

    expect(withId.id).toBe("keep");
    expect(withId.action_category).toBeUndefined();
  });

  it("sortNarrativeItemsInPlace() sorts by time_order or by text_span.start", () => {
    const items = [
      { id: "a", time_order: 2, text_span: { start: 50 } },
      { id: "b", time_order: 1, text_span: { start: 10 } },
      { id: "c", time_order: null, text_span: null }
    ];

    sortNarrativeItemsInPlace(items, true);
    expect(items.map((i) => i.id)).toEqual(["b", "a", "c"]);

    sortNarrativeItemsInPlace(items, false);
    expect(items.map((i) => i.id)).toEqual(["b", "a", "c"]);
  });

  it("findOriginalNarrativeIndexById() only matches objects by id", () => {
    const narrativeStructure = [
      "string",
      { id: "a", description: "x" },
      { id: "b", description: "y" }
    ];
    expect(findOriginalNarrativeIndexById(narrativeStructure, "b")).toBe(2);
    expect(findOriginalNarrativeIndexById(narrativeStructure, "missing")).toBe(-1);
  });

  it("removeNarrativeEntryById() removes only the matching object", () => {
    const narrativeStructure = [
      "string",
      { id: "a" },
      { id: "b" },
      { id: "a" }
    ];
    const next = removeNarrativeEntryById(narrativeStructure, "a");
    expect(next).toEqual(["string", { id: "b" }]);
  });

  it("buildNarrativeObjectFromString() matches updateItem conversion defaults", () => {
    const uuidFn = () => "newid";
    const obj = buildNarrativeObjectFromString({
      description: "legacy string",
      updates: { event_type: "ABSENTATION" },
      uuidFn,
      timeOrder: 123
    });

    expect(obj).toEqual({
      id: "newid",
      event_type: "ABSENTATION",
      description: "legacy string",
      agents: [],
      targets: [],
      text_span: null,
      target_type: "character",
      object_type: "",
      instrument: "",
      time_order: 123,
      relationship_level1: "",
      relationship_level2: "",
      relationship_multi: [],
      sentiment: ""
    });
  });

  it("applyNarrativeItemUpdate() falls back to updating sorted items when id missing", () => {
    const items = [{ description: "x" }];
    const narrativeStructure = [{ id: "orig", description: "orig" }];
    const next = applyNarrativeItemUpdate({
      items,
      narrativeStructure,
      index: 0,
      updates: { description: "updated" },
      uuidFn: () => "new",
      maxTimeOrder: 0
    });
    expect(next[0].description).toBe("updated");
  });

  it("applyNarrativeItemUpdate() updates original narrativeStructure entry by id", () => {
    const items = [{ id: "b", description: "sorted" }];
    const narrativeStructure = [{ id: "a", description: "a" }, { id: "b", description: "b" }];
    const next = applyNarrativeItemUpdate({
      items,
      narrativeStructure,
      index: 0,
      updates: { description: "B2" },
      uuidFn: () => "new",
      maxTimeOrder: 0
    });
    expect(next).toEqual([{ id: "a", description: "a" }, { id: "b", description: "B2" }]);
  });

  it("applyNarrativeItemUpdate() falls back to sorted items when id not found in original structure", () => {
    const items = [{ id: "missing", description: "sorted" }];
    const narrativeStructure = ["legacy", { id: "b", description: "b" }];
    const next = applyNarrativeItemUpdate({
      items,
      narrativeStructure,
      index: 0,
      updates: { description: "UPDATED" },
      uuidFn: () => "newid",
      maxTimeOrder: 10
    });
    expect(next).toEqual([{ id: "missing", description: "UPDATED" }]);
  });

  it("toggleNarrativeHighlightMap() toggles a single highlight entry", () => {
    const span = { start: 1, end: 2 };
    const first = toggleNarrativeHighlightMap({}, { idx: 0, span, color: "#60a5fa" });
    expect(first.isAdding).toBe(true);
    expect(first.next["narrative-0"]).toEqual({ start: 1, end: 2, color: "#60a5fa" });

    const second = toggleNarrativeHighlightMap(first.next, { idx: 0, span, color: "#60a5fa" });
    expect(second.isAdding).toBe(false);
    expect(second.next["narrative-0"]).toBeUndefined();
  });

  it("toggleAllNarrativeHighlightsMap() adds/removes all narrative highlights", () => {
    const items = [
      { text_span: { start: 10, end: 20 } },
      { text_span: null },
      { text_span: { start: 30, end: 40 } }
    ];

    const added = toggleAllNarrativeHighlightsMap({}, { items, allHighlighted: false, color: "#60a5fa" });
    expect(Object.keys(added).sort()).toEqual(["narrative-0", "narrative-2"]);

    const removed = toggleAllNarrativeHighlightsMap(added, { items, allHighlighted: true, color: "#60a5fa" });
    expect(removed["narrative-0"]).toBeUndefined();
    expect(removed["narrative-2"]).toBeUndefined();
  });

  it("computeAllNarrativeHighlighted() matches current filtered-index semantics", () => {
    const items = [
      { text_span: null },
      { text_span: { start: 1, end: 2 } },
      { text_span: { start: 3, end: 4 } }
    ];

    // NOTE: keys are narrative-0 and narrative-1 (indexes within the filtered list)
    const highlightedRanges = {
      "narrative-0": { start: 1, end: 2, color: "#60a5fa" },
      "narrative-1": { start: 3, end: 4, color: "#60a5fa" }
    };

    expect(computeAllNarrativeHighlighted({ highlightedRanges, items })).toBe(true);
    expect(computeAllNarrativeHighlighted({ highlightedRanges: null, items })).toBe(false);
    expect(computeAllNarrativeHighlighted({ highlightedRanges: {}, items: [] })).toBe(false);
  });

  it("narrativeHighlightKey()/narrativeHighlightMarkIdFromKey() keep the id format stable", () => {
    expect(narrativeHighlightKey(3)).toBe("narrative-3");
    expect(narrativeHighlightMarkIdFromKey("narrative-3")).toBe("narrative-3-mark");
  });

  it("relationship_multi list helpers add/update/remove rows", () => {
    const base = [
      { agent: "A", target: "T", relationship_level1: "L1", relationship_level2: "L2", sentiment: "pos" }
    ];

    const updated = updateRelationshipMultiRow(base, 0, { relationship_level1: "NEW" }, true);
    expect(updated[0].relationship_level1).toBe("NEW");
    expect(updated[0].relationship_level2).toBe("");

    const added = addRelationshipMultiRow(base, { agents: ["Solo"], targets: ["Only" ] });
    expect(added).toHaveLength(2);
    expect(added[1].agent).toBe("Solo");
    expect(added[1].target).toBe("Only");

    const removedToOne = removeRelationshipMultiRow(added, 1);
    expect(removedToOne).toHaveLength(1);

    const removedToEmpty = removeRelationshipMultiRow(base, 0);
    expect(removedToEmpty).toHaveLength(1);
    expect(removedToEmpty[0]).toEqual({ agent: "", target: "", relationship_level1: "", relationship_level2: "", sentiment: "" });
  });

  it("deriveRelationshipUiState() computes multiRel/rmList and effective levels", () => {
    const item = {
      target_type: "character",
      agents: ["A", "B"],
      targets: ["T"],
      relationship_level1: "LEGACY",
      relationship_level2: "LEGACY2",
      relationship_multi: [{ relationship_level1: "ROW", relationship_level2: "ROW2" }]
    };

    const state = deriveRelationshipUiState(item);
    expect(state.multiRel).toBe(true);
    expect(state.agents).toEqual(["A", "B"]);
    expect(state.targets).toEqual(["T"]);
    expect(state.rmList).toHaveLength(1);
    expect(state.rmList[0].relationship_level1).toBe("ROW");
    // multiRel prefers first relationship_multi row for effective level values
    expect(state.effectiveRelationshipLevel1).toBe("ROW");
    expect(state.effectiveRelationshipLevel2).toBe("ROW2");
  });

  it("buildSetRelationshipMultiUpdates() sets relationship_multi and clears legacy fields", () => {
    const updates = buildSetRelationshipMultiUpdates([{ agent: "A" }]);
    expect(updates.relationship_multi).toEqual([{ agent: "A" }]);
    expect(updates.relationship_level1).toBe("");
    expect(updates.relationship_level2).toBe("");
    expect(updates.sentiment).toBe("");
  });

});
