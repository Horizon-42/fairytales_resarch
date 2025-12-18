## 1. Action Categories Table

### I. Physical & Conflict
*Direct bodily interaction, violence, or movement.*

| Action Code | Definition | Recommended Context Tags |
| :--- | :--- | :--- |
| **`attack`** | Attempt to cause physical harm. | `ambush`, `duel`, `mass_battle`, `magical_blast` |
| **`defend`** | Block or mitigate harm. | `parry`, `shield`, `dodge` |
| **`restrain`** | Restrict physical freedom. | `bind`, `imprison`, `seal`, `arrest` |
| **`flee`** | Attempt to leave a dangerous area. | `panic`, `strategic_retreat`, `obstacle_flight` |
| **`steal`** | Take objects secretly. | `pickpocket`, `heist`, `switch` |
| **`travel`** | Significant change in location. | `quest_journey`, `flight`, `sneak` |

### II. Communicative & Social
*Information exchange and social manipulation.*

| Action Code | Definition | Recommended Context Tags |
| :--- | :--- | :--- |
| **`inform`** | Convey true information. | `report`, `rumor`, `confess` |
| **`persuade`** | Attempt to change views or behavior. | `advise`, `beg`, `seduce`, `debate` |
| **`deceive`** | Convey false information. | `disguise`, `lie`, `feign` |
| **`command`** | Force action via authority. | `decree`, `intimidation`, `task_assignment` |
| **`slander`** | Make false accusations. | `framing`, `court_intrigue`, `defamation` |
| **`promise`** | Establish a contract or credit. | `oath`, `marriage_proposal`, `contract` |

### III. Transaction & Exchange
*Transfer of resources or value.*

| Action Code | Definition | Recommended Context Tags |
| :--- | :--- | :--- |
| **`give`** | One-way transfer (A to B). | `alms`, `gift`, `inheritance` |
| **`request`** | Express desire for resources. | `demand`, `pray`, `borrow` |
| **`exchange`** | Two-way transfer. | `barter`, `buy`, `bribe` |
| **`reward`** | Positive feedback for behavior. | `promotion`, `title`, `treasure` |
| **`punish`** | Negative feedback for behavior. | `execution`, `exile`, `fine` |
| **`sacrifice`** | Give up value for moral/magic result. | `self_sacrifice`, `offering`, `martyrdom` |

### IV. Mental & Cognitive
*Internal state changes.*

| Action Code | Definition | Recommended Context Tags |
| :--- | :--- | :--- |
| **`observe`** | Acquire sensory info. | `spy`, `inspect`, `watch` |
| **`realize`** | Unknown to Known. | `epiphany`, `discovery`, `see_through` |
| **`investigate`** | Actively seek info. | `search`, `interrogate`, `track` |
| **`plot`** | Formulate plans internally. | `scheme`, `strategy`, `hesitate` |
| **`forget`** | Loss of info or ignoring. | `amnesia`, `ignore`, `magic_forgetfulness` |

### V. Existential & Magical
*Changes in state of being.*

| Action Code | Definition | Recommended Context Tags |
| :--- | :--- | :--- |
| **`transform`** | Change physical form. | `shapeshift`, `disguise_reveal`, `growth` |
| **`cast_spell`** | Release supernatural power. | `curse`, `bless`, `summon`, `heal` |
| **`express_emotion`**| Externalize strong emotion. | `cry`, `mourn`, `laugh`, `rage` |
| **`die`** | End of life cycle. | `suicide`, `natural_death`, `murdered` |
| **`revive`** | Return from death. | `resurrection`, `reincarnation`, `awakening` |

---

## 2. Status Codes (Execution Logic)

The **Status** field defines the outcome of the action code.

| Status Code | Logic |
| :--- | :--- |
| **`attempt`** | The action is initiated, but the result is not yet determined. |
| **`success`** | The action successfully achieved its intended goal. |
| **`failure`** | The action was blocked, dodged, or failed to produce an effect. |
| **`interrupted`** | The action was stopped by a third party or external event while in progress. |

---

## 3. JSON Schema Definition

```json
{
  "$schema": "[http://json-schema.org/draft-07/schema#](http://json-schema.org/draft-07/schema#)",
  "title": "Narrative Action Entry",
  "type": "object",
  "properties": {
    "agent": { "type": "string" },
    "target": { "type": "string" },
    "action_layer": {
      "type": "object",
      "properties": {
        "category": { 
          "type": "string",
          "enum": ["physical", "communicative", "transaction", "mental", "existential"]
        },
        "type": { "type": "string" },
        "context": { "type": "string" },
        "status": { 
          "type": "string", 
          "enum": ["attempt", "success", "failure", "interrupted"] 
        }
      },
      "required": ["category", "type", "status"]
    }
  }
}