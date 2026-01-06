import { describe, expect, it } from "vitest";
import { organizeFiles, mapV2ToState } from "./fileHandler.js";

// Mock File object
class MockFile {
  constructor(name, path) {
    this.name = name;
    this.webkitRelativePath = path;
  }
}

describe("fileHandler", () => {
  it("organizeFiles groups v1/v2 texts and jsons", () => {
    const files = [
      new MockFile("story1.txt", "dataset/texts/story1.txt"),
      new MockFile("story2.txt", "dataset/texts/story2.txt"),
      new MockFile("story1.json", "dataset/json/story1.json"),
      new MockFile("story1.json", "dataset/json_v2/story1.json"), // V2 in folder
      new MockFile("story2_v2.json", "dataset/json/story2_v2.json"), // V2 by suffix
    ];

    const { texts, v1Jsons, v2Jsons } = organizeFiles(files);

    expect(texts.length).toBe(2);
    expect(texts[0].id).toBe("story1");
    expect(!!v1Jsons["story1"]).toBe(true);
    expect(!!v2Jsons["story1"]).toBe(true);
    expect(!!v2Jsons["story2"]).toBe(true);
  });

  it("mapV2ToState maps key fields", () => {
    const v2Data = {
      version: "2.0",
      metadata: { id: "test", culture: "TestCulture" },
      characters: [{ name: "Hero", archetype: "The Hero" }],
      themes_and_motifs: { atu_type: "300" },
      analysis: { propp_functions: [{ fn: "A" }] }
    };

    const state = mapV2ToState(v2Data);
    expect(state.id).toBe("test");
    expect(state.culture).toBe("TestCulture");
    expect(state.motif.character_archetypes[0].name).toBe("Hero");
    expect(state.meta.atu_type).toBe("300");
    expect(state.proppFns[0].fn).toBe("A");
  });
});

