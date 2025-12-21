# Fairytale Visualization Framework

An interactive visualization framework for exploring Chinese fairytale narratives, built with React and D3.js.

## Overview

This framework provides two main visualizations:

1. **Character Relationship Graph** - Force-directed network graph showing character connections
2. **Story Ribbons** - Timeline visualization showing character interactions through the narrative

## Technologies

- **React 18** - UI framework
- **D3.js v7** - Data visualization library
- **Vite** - Build tool and dev server
- **React Router** - Page navigation

## Quick Start

```bash
# Install dependencies
cd visualization
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

The app runs on `http://localhost:5173` (or next available port).

---

## Project Structure

```
visualization/
├── public/
│   └── data/                    # Generated visualization data
│       ├── stories_index.json   # Index of all stories
│       ├── *_relationships.json # Character graph data
│       └── *_ribbons.json       # Story ribbon data
├── src/
│   ├── pages/
│   │   ├── CharacterGraph.jsx   # Relationship graph visualization
│   │   ├── CharacterGraph.css
│   │   ├── StoryRibbons.jsx     # Story ribbons visualization
│   │   └── StoryRibbons.css
│   ├── styles/
│   │   └── App.css              # Global styles and CSS variables
│   ├── App.jsx                  # Main app with routing
│   └── main.jsx                 # Entry point
├── index.html
├── package.json
└── vite.config.js
```

---

## Pages

### Character Graph (`/graph`)

An interactive force-directed graph showing character relationships.

#### Features

- **Nodes**: Characters sized by interaction count
- **Edges**: Relationships colored by type, weighted by interaction frequency
- **Interactivity**: 
  - Drag nodes to rearrange
  - Hover for character/relationship details
  - Click nodes to highlight connections

#### Visual Encoding

**Node Colors (by Archetype):**
| Archetype | Color | Hex |
|-----------|-------|-----|
| Hero | Crimson | #DC143C |
| Villain | Dark Purple | #4B0082 |
| Mentor | Forest Green | #228B22 |
| Sidekick/Helper | Sky Blue | #87CEEB |
| Lover | Rose Pink | #FF69B4 |
| Guardian | Steel Blue | #4682B4 |
| Trickster | Orange | #FF8C00 |
| Threshold Guardian | Brown | #8B4513 |
| Herald | Gold | #FFD700 |
| Shapeshifter | Purple | #9932CC |
| Shadow | Dark Gray | #2F4F4F |
| Everyman | Tan | #D2B48C |
| Innocent | Light Pink | #FFB6C1 |
| Explorer | Teal | #008080 |
| Ruler | Royal Blue | #4169E1 |
| Other | Gray | #808080 |

**Edge Colors (by Relationship Type):**
| Relationship | Color | Hex |
|--------------|-------|-----|
| Family & Kinship | Warm Brown | #8B4513 |
| Romance | Rose Pink | #E91E63 |
| Adversarial | Dark Red | #B71C1C |
| Social/Hierarchical | Navy Blue | #1565C0 |
| Supernatural | Deep Purple | #6A1B9A |
| Transformative | Teal | #00838F |

#### Legend

The legend (collapsible) shows:
- Character archetypes with colors
- Relationship types with colors

---

### Story Ribbons (`/ribbons`)

A timeline visualization showing how characters interact through the narrative.

#### Layout

```
Y-Axis (Characters)                    X-Axis (Narrative Events)
                                       Event 1  Event 2  Event 3  ...
┌─────────────────────────────────────────────────────────────────────┐
│  Friendly Characters (low centrality)   ═══════════════════════    │
│  Friendly Characters (mid centrality)      ════╗    ╔════════      │
│  Friendly Characters (high centrality)   ══════╬════╬══════════    │
│  ★ HERO (center)                         ══════╬════╬══════════    │
│  Hostile Characters (high centrality)    ══════╝    ╚══════════    │
│  Hostile Characters (mid centrality)       ════════════════════    │
│  Hostile Characters (low centrality)    ═══════════════════════    │
└─────────────────────────────────────────────────────────────────────┘
```

#### Visual Encoding

**Character Position (Y-axis):**
- **Center**: Main hero (identified by centrality among Hero archetypes)
- **Above hero**: Friendly characters (sorted by centrality - highest closest to hero)
- **Below hero**: Hostile characters (sorted by centrality - highest closest to hero)

**Ribbon Colors - Gradient System:**

The ribbons now use a **gradient coloring system** that shows sentiment changes over time:

| Component | Color Logic |
|-----------|-------------|
| **Center Line** | Camp color (stable) - based on overall friendly/hostile classification |
| **Ribbon Fill** | Gradient showing sentiment progression through narrative |

**Sentiment-to-Color Mapping:**
| Friendly Level | Color | Sentiment |
|----------------|-------|-----------|
| +2 | #e63946 (Vermillion) | romantic |
| +1 | #f77f00 (Orange) | positive |
| 0 | #9ca3af (Gray) | neutral |
| -1 | #457b9d (Steel Blue) | negative |
| -2 | #370617 (Dark Crimson) | hostile, fearful |

**How Gradients Work:**
1. First interaction's level determines starting color
2. Each event updates the cumulative friendliness
3. Ribbon fill interpolates colors based on cumulative level at each event
4. Center line stays in camp color (stable reference)

**Camp Colors (for center line):**
| Character Type | Color Scheme | Example Colors |
|----------------|--------------|----------------|
| Hero | Vermillion Red | #e63946 |
| Friendly | Warm palette | #f4a261, #e76f51, #ffc300, #fb8500 |
| Hostile | Cool palette | #370617, #0077b6, #457b9d, #023e8a |
| Neutral | Gray palette | #6b6b6b, #9ca3af |

**Ribbon Movement:**
- **Agent (Active)**: Ribbon stays at home position (filled dot marker)
- **Target (Passive)**: Ribbon curves toward the agent's position (hollow dot marker)

**Multi-Agent Events:**
When multiple agents are involved:
1. Calculate average Y-coordinate of all agents as "anchor"
2. Agent ribbons move 70% toward anchor
3. Target ribbons move 90% toward anchor

#### Interactivity

- **Hover on ribbon**: Highlight character, show info in legend
- **Hover on event marker**: Show event details panel
- **Legend toggle**: Click "? Legend" to show/hide explanation

#### Event Type Colors

| Event Type | Color |
|------------|-------|
| Villainy | #d32f2f |
| Lack | #f57c00 |
| Guidance | #388e3c |
| Struggle | #7b1fa2 |
| Victory | #1976d2 |
| Solution | #00796b |
| Other | #757575 |

---

## Data Requirements

The visualization expects data in `public/data/` directory:

### `stories_index.json`
```json
{
  "stories": [
    {
      "id": "CH_002_牛郎织女",
      "title": "牛郎织女",
      "character_count": 10,
      "event_count": 13,
      "relationship_file": "CH_002_牛郎织女_relationships.json",
      "ribbon_file": "CH_002_牛郎织女_ribbons.json"
    }
  ]
}
```

### Relationship Data (`*_relationships.json`)
```json
{
  "nodes": [
    { "id": "char_0", "name": "牛郎", "archetype": "Hero" }
  ],
  "edges": [
    {
      "source": "char_0",
      "target": "char_1",
      "weight": 5,
      "relationship_type": "Romance",
      "sentiment": "romantic"
    }
  ]
}
```

### Ribbon Data (`*_ribbons.json`)
```json
{
  "title": "牛郎织女",
  "characters": [
    {
      "name": "牛郎",
      "centrality": 0.533,
      "hero_relationship": "hero",
      "display_order": 5
    }
  ],
  "events": [
    {
      "time_order": 1,
      "event_type": "VILLAINY",
      "agents": ["天帝"],
      "targets": ["牛郎", "织女"],
      "sentiment": "hostile"
    }
  ]
}
```

---

## Generating Data

Data is generated by the Python post-processing scripts:

```bash
# From project root
cd /path/to/fairytales_resarch

# Activate environment with networkx
conda activate nlp

# Run processing
python3 post_data_process/process_json_for_viz.py
```

See `post_data_process/README.md` for detailed documentation.

---

## CSS Variables

The app uses CSS custom properties defined in `src/styles/App.css`:

```css
:root {
  /* Colors */
  --ink-black: #1a1a1a;
  --ink-dark: #333;
  --ink-medium: #666;
  --ink-light: #999;
  
  --paper-cream: #f5f0e6;
  --paper-warm: #e8e0d0;
  --paper-light: #faf8f5;
  
  --gold: #c4a35a;
  --gold-light: #d4b87a;
  --vermillion: #e63946;
  
  /* Typography */
  --font-chinese: "Noto Serif SC", "Source Han Serif CN";
  --font-serif: Georgia, "Times New Roman", serif;
  --font-sans: "Inter", -apple-system, sans-serif;
  
  /* Spacing */
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;
  
  /* Shadows */
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.1);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.1);
}
```

---

## Customization

### Adding New Stories

1. Add source JSON to `datasets/ChineseTales/json_v2/`
2. Run `python3 post_data_process/process_json_for_viz.py`
3. New story appears in dropdown automatically

### Modifying Color Schemes

**Character Graph colors:** Edit `archetypeColors` and `relationshipColors` in `CharacterGraph.jsx`

**Story Ribbons colors:** Edit color palettes in `StoryRibbons.jsx`:
```javascript
const heroColor = '#e63946'
const warmColorPalette = ['#f4a261', '#e76f51', '#ffc300', ...]
const coolColorPalette = ['#370617', '#0077b6', '#457b9d', ...]
```

### Adjusting Ribbon Behavior

In `StoryRibbons.jsx`:
```javascript
// How much targets move toward agents (0-1)
const pullStrength = 0.9

// For multi-agent events:
const agentPullStrength = 0.7   // Agents move 70% toward anchor
const targetPullStrength = 0.9  // Targets move 90% toward anchor
```

---

## Browser Support

- Chrome/Edge (recommended)
- Firefox
- Safari

SVG-based visualizations require modern browser support.

---

## Troubleshooting

### Data not loading
- Ensure `public/data/stories_index.json` exists
- Check browser console for fetch errors
- Verify JSON files are valid

### Ribbons not rendering
- Check that `characters` array has `display_order` field
- Verify `events` have `time_order` > 0

### Graph layout issues
- Try refreshing - force simulation has random initialization
- Adjust force parameters in `CharacterGraph.jsx`

### Chinese characters not displaying
- Install Chinese fonts (Noto Serif SC recommended)
- Check `font-family` fallbacks in CSS

