## 1. Action Categories

### I. Physical & Conflict
*Direct bodily interaction, violence, or movement.*

| Code | Definition | Recommended Context Tags |
| :--- | :--- | :--- |
| **`attack`** | Attempt to cause physical harm. | `ambush`, `duel`, `spar`, `brawl`, `mass_battle`, `magical_blast` |
| **`defend`** | Block or mitigate harm. | `parry`, `shield`, `dodge`, `bracing` |
| **`restrain`** | Restrict physical freedom. | `bind`, `imprison`, `pin_down`, `arrest`, `seal` |
| **`flee`** | Attempt to leave a dangerous area. | `panic`, `strategic_retreat`, `escape`, `obstacle_flight` |
| **`travel`** | Significant change in location. | `quest`, `quest_journey`, `sneak`, `chase`, `wander`, `flight` |
| **`interact`** | Manipulate physical objects/environment. | `consume`, `repair`, `destroy_obj`, `craft` |
| **`steal`** | (Compatibility) Take property/resources without consent. | `pickpocket`, `heist`, `switch` |

### II. Social & Communicative
*Information exchange, relationship dynamics, and verbal acts.*

| Code | Definition | Recommended Context Tags |
| :--- | :--- | :--- |
| **`inform`** | Convey true/neutral information. | `report`, `reveal`, `explain`, `confess`, `rumor` |
| **`persuade`** | Attempt to influence logic or behavior. | `advise`, `beg`, `negotiate`, `seduce`, `debate` |
| **`deceive`** | Convey false info to manipulate. | `lie`, `feign`, `disguise`, `mislead` |
| **`challenge`** | Initiate conflict or competition. | `provoke`, `duel_proposal`, `threaten` |
| **`command`** | Force action via authority. | `order`, `decree`, `coerce`, `assign_task`, `intimidation`, `task_assignment` |
| **`betray`** | Break established trust or allegiance. | `backstab`, `defect`, `break_oath` |
| **`reconcile`** | Restore relationship or reduce tension. | `apologize`, `comfort`, `forgive`, `mediate` |
| **`slander`** | (Compatibility) Damage reputation via false accusations. | `framing`, `court_intrigue`, `defamation` |
| **`promise`** | (Compatibility) Commit to a future action/guarantee. | `oath`, `marriage_proposal`, `contract` |

### III. Transaction & Exchange
*Transfer of resources, status, or value.*

| Code | Definition | Recommended Context Tags |
| :--- | :--- | :--- |
| **`give`** | One-way resource transfer (outgoing). | `gift`, `alms`, `legacy`, `supply`, `inheritance` |
| **`acquire`** | One-way resource transfer (incoming). | `steal`, `borrow`, `seize`, `loot` |
| **`exchange`** | Two-way transfer. | `trade`, `barter`, `bribe`, `buy` |
| **`reward`** | Positive feedback/payment for service. | `promote`, `pay`, `honor`, `bless`, `promotion`, `title`, `treasure` |
| **`punish`** | Negative feedback/penalty for behavior. | `fine`, `exile`, `execution`, `demote` |
| **`request`** | (Compatibility) Ask for resources, help, or permission. | `demand`, `pray`, `borrow` |
| **`sacrifice`** | (Compatibility) Give up something valuable (often self/offerings) for a goal or higher power. | `self_sacrifice`, `offering`, `martyrdom` |

### IV. Mental & Cognitive
*Internal state changes and decision making processes.*

| Code | Definition | Recommended Context Tags |
| :--- | :--- | :--- |
| **`resolve`** | Firm commitment to a goal/action. | `decide`, `vow`, `steel_oneself`, `harden_heart` |
| **`plan`** | Formulate future strategy. | `scheme`, `strategize`, `plot`, `strategy` |
| **`realize`** | Shift from unknown to known. | `epiphany`, `detect`, `deduce`, `discovery`, `see_through` |
| **`hesitate`** | Loss of confidence or direction. | `doubt`, `fear`, `waver`, `confuse` |
| **`observe`** | (Compatibility) Watch closely to gather information. | `spy`, `inspect`, `watch` |
| **`investigate`** | (Compatibility) Systematically search for facts/truth. | `search`, `interrogate`, `track` |
| **`plot`** | (Compatibility) Scheme in secret (legacy code; overlaps with `plan`). | `scheme`, `strategy`, `hesitate` |
| **`forget`** | (Compatibility) Lose or suppress memory/knowledge. | `amnesia`, `ignore`, `magic_forgetfulness` |

### V. Existential & Supernatural
*Changes in state of being or magical acts.*

| Code | Definition | Recommended Context Tags |
| :--- | :--- | :--- |
| **`cast`** | Release supernatural power. | `curse`, `heal`, `summon`, `enchant`, `bless` |
| **`transform`** | Change physical form. | `shapeshift`, `grow`, `shrink`, `disguise_reveal`, `growth` |
| **`die`** | End of life cycle. | `sacrifice`, `perish`, `murdered`, `suicide`, `natural_death` |
| **`revive`** | Return to active state. | `awaken`, `resurrect`, `regenerate`, `resurrection`, `reincarnation`, `awakening` |
| **`cast_spell`** | (Compatibility) Cast a spell (legacy code; overlaps with `cast`). | `curse`, `bless`, `summon`, `heal` |
| **`express_emotion`** | (Compatibility) Express strong emotion outwardly. | `cry`, `mourn`, `laugh`, `rage` |

---

## 2. Status & Logic Layer

*Describes the outcome or execution state of the action.*

| Tag | Definition |
| :--- | :--- |
| **`attempt`** | Action initiated, outcome pending or unknown. |
| **`success`** | Action achieved its intended goal. |
| **`failure`** | Action failed to achieve its goal. |
| **`interrupted`**| Action stopped by external force before completion. |
| **`backfire`** | Action produced a result opposite to intent (harmful to agent). |
| **`partial`** | Action achieved some goals but not all. |

---

## 3. Narrative Function Layer

*Describes the action's role in the story structure.*

* **`trigger`**: An event that initiates a new plot line or conflict.
* **`climax`**: The highest point of tension or conflict.
* **`resolution`**: The action that resolves a conflict.
* **`character_arc`**: An action defining a shift in personality or belief.
* **`setup`**: Preparation for future events.
* **`exposition`**: Action serving primarily to reveal background info.