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
Determines if each character is friendly or hostile to the hero using a voting system.

**Voting Rules:**
| Scenario | Vote |
|----------|------|
| Character is AGENT, hero is TARGET, sentiment=positive | Friendly |
| Character is AGENT, hero is TARGET, sentiment=hostile | Hostile |
| Hero is AGENT, character is TARGET, sentiment=hostile | Hostile |
| Hero is AGENT, character is TARGET, sentiment=positive | *Ignored* |

**Classification Logic:**
- `friendly_votes > hostile_votes` → **Friendly**
- `hostile_votes > friendly_votes` → **Hostile**
- Equal votes → Use the **later (more recent)** interaction's sentiment
- No interactions → Default to **Friendly**

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

| Character | Centrality | Votes | Classification | Reason |
|-----------|------------|-------|----------------|--------|
| 牛郎 | 0.533 | - | **Hero** | Highest centrality Hero archetype |
| 织女 | 0.267 | 0F/0H | Friendly | Default (no negative actions) |
| 老牛 | 0.133 | 3F/0H | Friendly | Mentor who helps hero |
| 王母娘娘 | 0.400 | 0F/2H | Hostile | Separates the couple |
| 天帝 | 0.200 | 0F/1H | Hostile | Antagonist authority |
| 哥嫂 | 0.067 | 0F/1H | Hostile | Mistreats the hero |

### 梁山伯与祝英台 (Butterfly Lovers)

| Character | Centrality | Votes | Classification | Reason |
|-----------|------------|-------|----------------|--------|
| 祝英台 | 0.429 | - | **Hero** | Highest centrality Hero archetype |
| 梁山伯 | 0.171 | 5F/0H | Friendly | The lover |
| 祝员外 | 0.257 | 0F/5H | Hostile | Forces arranged marriage |
| 马文才 | 0.086 | 0F/2H | Hostile | The antagonist suitor |

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

### Sentiment Classification

| Sentiment Values | Classification |
|------------------|----------------|
| positive, romantic, respectful, grateful | Friendly |
| negative, hostile, fearful, antagonistic | Hostile |
| neutral, (empty) | Neutral |

### Tie-Breaking for Equal Votes

When `friendly_votes == hostile_votes`:
1. Find the most recent interaction (highest `time_order`)
2. Use that interaction's sentiment
3. If neutral or no interactions → Default to Friendly

