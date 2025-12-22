# Post Data Process

This directory contains Python scripts for transforming raw fairytale JSON data into visualization-ready formats.

## Overview

The data processing pipeline takes structured fairytale narratives (from `datasets/ChineseTales/json_v2/`) and generates two types of visualization data:

1. **Character Relationship Data** - Node-edge graph for relationship visualization
2. **Story Ribbon Data** - Timeline data with character involvement and interactions

## Scripts

### `process_json_for_viz.py`

The main entry point that orchestrates the data transformation pipeline.

**Usage:**
```bash
# Using default paths
python3 post_data_process/process_json_for_viz.py

# Custom input/output paths
python3 post_data_process/process_json_for_viz.py <input_dir> <output_dir>
```

**Default Paths:**
- Input: `datasets/ChineseTales/json_v2/`
- Output: `visualization/public/data/`

**Output Files:**
For each story (e.g., `CH_002_牛郎织女`):
- `CH_002_牛郎织女_relationships.json` - Character graph data
- `CH_002_牛郎织女_ribbons.json` - Story ribbon data
- `stories_index.json` - Index of all processed stories

---

### `character_analysis.py`

Core module for analyzing character relationships and sorting characters for visualization.

#### Key Functions

##### `build_interaction_graph(events, characters)`
Builds a NetworkX graph from character interactions.
- **Input:** Narrative events and character list
- **Output:** Weighted undirected graph where edge weights = interaction frequency

##### `calculate_centrality(G)`
Calculates combined centrality scores for character importance.
- Uses 60% degree centrality + 40% eigenvector centrality
- Falls back to simple degree if eigenvector calculation fails

##### `identify_main_hero(characters, centrality)`
Identifies the protagonist based on:
1. Characters with "Hero" archetype
2. Among heroes, the one with highest centrality
3. If no heroes, character with highest overall centrality

##### `analyze_character_relationships_voting(events, characters, hero_name)`
Determines if each character is friendly or hostile to the hero using a voting system based on **direct interactions only**.

**Direct Interaction Rules:**
| Scenario | Friendly Level | Effect |
|----------|----------------|--------|
| Character is AGENT → Hero is TARGET, positive | +1 to +2 | Adds to friendly total |
| Character is AGENT → Hero is TARGET, hostile | -1 to -2 | Adds to hostile total |
| Hero is AGENT → Character is TARGET, hostile | -1 to -2 | Marks character as hostile |
| Hero is AGENT → Character is TARGET, positive | *Ignored* | Hero helping doesn't change classification |
| **Co-participants (both agents or both targets)** | **Ignored** | Not a direct interaction |

**Important:** When a third party attacks both the hero and another character (e.g., 天帝 attacks 牛郎 and 织女), the other character (织女) is NOT marked as hostile - they are a fellow victim, not an enemy.

**Classification Logic:**
- `total_level > 0` → **Friendly camp**
- `total_level < 0` → **Hostile camp**
- `total_level == 0` → Use the **most recent** interaction's level; default to Friendly

##### `sort_characters_for_ribbon(characters, centrality, hero_analysis, hero_name)`
Sorts characters for Y-axis positioning in ribbon visualization:

```
Top (furthest from hero)
    ↓ Friendly characters (sorted by centrality: low → high)
    ↓ 
  ★ HERO (center)
    ↓
    ↓ Hostile characters (sorted by centrality: high → low)
Bottom (furthest from hero)
```

**Positioning Logic:**
- Higher centrality = closer to hero
- Friendly characters above hero
- Hostile characters below hero

---

## Data Formats

### Input Format (from `json_v2/*.json`)

```json
{
  "metadata": {
    "id": "CH_002",
    "title": "牛郎织女"
  },
  "characters": [
    {
      "name": "牛郎",
      "alias": "牛郎;Cowherd",
      "archetype": "Hero"
    }
  ],
  "narrative_events": [
    {
      "id": "event_1",
      "time_order": 1,
      "event_type": "VILLAINY",
      "description": "...",
      "agents": ["天帝"],
      "targets": ["牛郎", "织女"],
      "sentiment": "hostile",
      "relationship_level1": "Adversarial",
      "text_span": { "start": 0, "end": 100, "text": "..." }
    }
  ]
}
```

### Output: Relationship Data (`*_relationships.json`)

```json
{
  "nodes": [
    {
      "id": "char_0",
      "name": "牛郎",
      "alias": "",
      "archetype": "Hero"
    }
  ],
  "edges": [
    {
      "source": "char_0",
      "target": "char_1",
      "weight": 5,
      "relationship_type": "Romance",
      "sentiment": "romantic",
      "interactions": [...]
    }
  ]
}
```

### Output: Ribbon Data (`*_ribbons.json`)

```json
{
  "title": "牛郎织女",
  "id": "CH_002",
  "characters": [
    {
      "id": "char_0",
      "name": "妇女们",
      "archetype": "Other",
      "centrality": 0.0,
      "affinity_score": 0.0,
      "hero_relationship": "friendly",
      "is_main_hero": false,
      "friendly_count": 0,
      "hostile_count": 0,
      "display_order": 0
    },
    {
      "id": "char_6",
      "name": "牛郎",
      "archetype": "Hero",
      "centrality": 0.533,
      "hero_relationship": "hero",
      "is_main_hero": true,
      "display_order": 5
    }
  ],
  "events": [
    {
      "id": "event_1",
      "time_order": 1,
      "event_type": "VILLAINY",
      "description": "...",
      "agents": ["天帝"],
      "targets": ["牛郎", "织女"],
      "sentiment": "hostile"
    }
  ],
  "total_events": 13,
  "analysis": {
    "main_hero": "牛郎",
    "hero_centrality": 0.533,
    "total_characters": 10,
    "friendly_count": 5,
    "hostile_count": 4
  }
}
```

---

## Character Classification Examples

### 牛郎织女 (The Cowherd and the Weaver Girl)

| Character | Centrality | Total Level | Direct Interactions | Classification | Reason |
|-----------|------------|-------------|---------------------|----------------|--------|
| 牛郎 | 0.533 | - | - | **Hero** | Highest centrality Hero archetype |
| 织女 | 0.267 | 0 | 0 | Friendly | No direct interaction with hero (co-participant only) |
| 老牛 | 0.133 | +3 | 3 | Friendly | Mentor who helps hero 3 times |
| 王母娘娘 | 0.400 | -4 | 2 | Hostile | Attacks hero twice |
| 天帝 | 0.200 | -2 | 1 | Hostile | Attacks hero once |
| 天神 | - | -2 | 1 | Hostile | Attacks hero once |
| 哥嫂 | 0.067 | -1 | 1 | Hostile | Mistreats the hero |

**Note:** 织女 appears in many events with 牛郎 but always as co-participants (both targets or both agents). She has NO direct interactions where she acts on 牛郎 or vice versa, so her `total_level = 0` and she defaults to friendly.

### 梁山伯与祝英台 (Butterfly Lovers)

| Character | Centrality | Total Level | Classification | Reason |
|-----------|------------|-------------|----------------|--------|
| 祝英台 | 0.429 | - | **Hero** | Highest centrality Hero archetype |
| 梁山伯 | 0.171 | +N | Friendly | The lover with positive interactions |
| 祝员外 | 0.257 | -N | Hostile | Forces arranged marriage |
| 马文才 | 0.086 | -N | Hostile | The antagonist suitor |

---

## Dependencies

```
networkx>=3.0
```

Install with:
```bash
pip install networkx
# or with conda
conda install networkx
```

---

## Algorithm Details

### Centrality Calculation

The centrality score combines two measures:

1. **Degree Centrality (60%)**: Number of unique characters a character interacts with, normalized by total characters.

2. **Eigenvector Centrality (40%)**: Importance based on connections to other important characters (PageRank-like).

```python
centrality = 0.6 * degree_centrality + 0.4 * eigenvector_centrality
```

### Friendly Level Values

Based on `docs/Character_Resources/sentiment.csv`:

| Sentiment | Friendly Level | Description |
|-----------|---------------|-------------|
| romantic | +2 | High positive (love, deep affection) |
| positive | +1 | Positive (trust, gratitude, help) |
| neutral | +1 | Neutral (default to friendly) |
| negative | -1 | Negative (mockery, rejection) |
| fearful | -2 | High negative (fear, submission) |
| hostile | -2 | High negative (attack, intent to harm) |

### Camp Classification Logic

1. Sum friendly levels from all interactions (only when character is AGENT towards hero)
2. If hero attacks character (hero is AGENT with negative sentiment), add negative levels
3. `total_level > 0` → **Friendly camp**
4. `total_level < 0` → **Hostile camp**
5. `total_level == 0` → Use last interaction's level; default to friendly

### Tie-Breaking for Equal Levels

When `total_level == 0`:
1. Find the most recent interaction (highest `time_order`)
2. Use that interaction's friendly level
3. If neutral or no interactions → Default to Friendly

### Per-Event Friendliness (for Gradient Coloring)

Each character tracks friendliness **only for events where they have direct interaction with the hero**:

```python
{
    'time_order': 8,           # When this event occurred
    'friendly_level': -2,       # Level at this specific event
    'cumulative_level': -4,     # Running total of all levels
    'sentiment': 'hostile'      # Raw sentiment value
}
```

**Direct Interaction Definition:**
- Character is AGENT acting on HERO (target)
- HERO is AGENT acting on character (target)

**NOT Direct Interaction (excluded):**
- Co-participants: Both are agents in same event
- Co-victims: Both are targets in same event (e.g., villain attacks hero AND friend)

This ensures that ribbon gradient colors accurately reflect each character's relationship with the hero, not third-party actions.

