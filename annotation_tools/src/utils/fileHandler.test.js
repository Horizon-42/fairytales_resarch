
import { organizeFiles, mapV2ToState, mapV1ToState } from './fileHandler.js';
import assert from 'assert';

console.log("Running fileHandler tests...");

// Mock File object
class MockFile {
  constructor(name, path) {
    this.name = name;
    this.webkitRelativePath = path;
  }
}

// Test 1: organizeFiles
{
  const files = [
    new MockFile('story1.txt', 'dataset/texts/story1.txt'),
    new MockFile('story2.txt', 'dataset/texts/story2.txt'),
    new MockFile('story1.json', 'dataset/json/story1.json'),
    new MockFile('story1.json', 'dataset/json_v2/story1.json'), // V2 in folder
    new MockFile('story2_v2.json', 'dataset/json/story2_v2.json'), // V2 by suffix
  ];

  const { texts, v1Jsons, v2Jsons } = organizeFiles(files);

  assert.strictEqual(texts.length, 2);
  assert.strictEqual(texts[0].id, 'story1');
  
  // story1 has both, but organizeFiles just groups them. 
  // Wait, organizeFiles keys by ID.
  assert.ok(v1Jsons['story1'], 'Should find V1 for story1');
  assert.ok(v2Jsons['story1'], 'Should find V2 for story1');
  assert.ok(v2Jsons['story2'], 'Should find V2 for story2 (suffix)');
  
  console.log("Test 1 Passed: organizeFiles");
}

// Test 2: mapV2ToState
{
  const v2Data = {
    version: "2.0",
    metadata: { id: "test", culture: "TestCulture" },
    characters: [{ name: "Hero", archetype: "The Hero" }],
    themes_and_motifs: { atu_type: "300" },
    analysis: { propp_functions: [{ fn: "A" }] }
  };

  const state = mapV2ToState(v2Data);
  assert.strictEqual(state.id, "test");
  assert.strictEqual(state.culture, "TestCulture");
  assert.strictEqual(state.motif.character_archetypes[0].name, "Hero");
  assert.strictEqual(state.meta.atu_type, "300");
  assert.strictEqual(state.proppFns[0].fn, "A");

  console.log("Test 2 Passed: mapV2ToState");
}

console.log("All tests passed!");

