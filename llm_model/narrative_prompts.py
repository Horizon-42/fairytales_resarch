from __future__ import annotations

import json
from typing import Any, Dict, List, Literal, Optional

# Guidelines derived from resource files
PROPP_GUIDE = """
### 1. Event Type (Propp's Functions)
Classify the event using Vladimir Propp's Morphology. Focus on the structural role, not literal interpretation.
If the event fits no specific function, use "OTHER".

Key Functions (Select one symbol/code):
- alpha (Initial Situation): Intro of hero/family.
- beta (Absentation): Authority leaves; vacuum of order.
- gamma (Interdiction): Hero is warned.
- delta (Violation): Rule broken; villain enters.
- epsilon (Reconnaissance): Villain gathers info.
- zeta (Delivery): Villain gets info.
- eta (Trickery): Villain deceives victim.
- theta (Complicity): Victim submits to deception.
- A (Villainy): Villain causes harm/theft (Driver Type 1).
- a (Lack): Family lacks something (Driver Type 2).
- B (Mediation): Hero is dispatched/approached.
- C (Counteraction): Hero decides to act.
- arrow_up (Departure): Hero leaves home.
- D (1st Function of Donor): Hero is tested by potential donor.
- E (Hero's Reaction): Hero responds to test.
- F (Receipt of Agent): Hero acquires magical item/helper.
- G (Guidance): Hero transferred to location.
- H (Struggle): Direct combat with villain.
- J (Branding): Hero is wounded/marked.
- I (Victory): Villain defeated.
- K (Liquidation): Initial lack/villainy resolved.
- arrow_down (Return): Hero returns.
- Pr (Pursuit): Hero is pursued.
- Rs (Rescue): Hero rescued from pursuit.
- o (Unrecognized Arrival): Arrives in disguise.
- L (Unfounded Claims): False hero claims prize.
- M (Difficult Task): Task proposed to hero.
- N (Solution): Task resolved.
- Q (Recognition): Hero recognized.
- Ex (Exposure): False hero/villain exposed.
- T (Transfiguration): Hero given new appearance/status.
- U (Punishment): Villain punished.
- W (Wedding): Ultimate reward/status elevation.
"""

RELATIONSHIP_GUIDE = """
### 2. Relationships
If the target is a character, define the relationship (Level 1 & Level 2) based on social context:

* **Family & Kinship**
  - `parent_child`: Vertical upbringing/authority (inc. adoption).
  - `sibling`: Horizontal blood/sworn relation (often competitive).
  - `spouse`: Legal/customary long-term partner (contractual).
  - `extended_family`: Non-direct kin (Uncle, Aunt, Grandparent).

* **Romance**
  - `lover`: Passion-based, non-marital (inc. affairs, courtly love).

* **Hierarchy**
  - `ruler_subject`: Political rule based on law/territory.
  - `master_servant`: Ownership/monetary dominance (Employer/Employee).
  - `mentor_student`: Knowledge/Wisdom transmission.
  - `commander_subordinate`: Organized chain of command (Military/Gang).

* **Social & Alliance**
  - `friend`: Personal intimacy, non-utilitarian.
  - `ally`: Shared goal/interest (temporary or long-term).
  - `colleague`: Professional peers or shared mentorship.

* **Adversarial**
  - `enemy`: Existential hatred, goal is destruction/death.
  - `rival`: Competitive (honor/prize), not necessarily lethal.

* **Neutral**
  - `stranger`: No prior social interaction.
"""

SENTIMENT_GUIDE = """
### 3. Sentiment
Annotate the emotional state of the Agent toward the Target in this specific event.
*Note: Sentiment can contradict Relationship (e.g., enemies falling in love).*

- `romantic` (High Positive): Courtship, sexual attraction, deep affection.
- `positive` (Friendly): Trust, gratitude, respect, help.
- `neutral` (Indifferent): Transactional, emotionless, passing by.
- `negative` (Dislike): Mockery, rejection, impatience, scorn.
- `fearful` (Submissive): Trembling, begging, forced submission.
- `hostile` (High Negative): Murderous intent, rage, cursing, attack.
"""

ACTION_GUIDE = """
### 4. Action Category (Universal Taxonomy)
Mandatory field. Select the most appropriate Category and Type.

Use these exact category codes:
* `physical` (Physical & Conflict)
* `communicative` (Social & Communicative)
* `transaction` (Transaction & Exchange)
* `mental` (Mental & Cognitive)
* `existential` (Existential & Supernatural)

Action types must be the exact code under the chosen category. Common examples:
* `physical`: `attack`, `defend`, `restrain`, `flee`, `travel`, `interact`
* `communicative`: `inform`, `persuade`, `deceive`, `challenge`, `command`, `betray`, `reconcile`
* `transaction`: `give`, `acquire`, `exchange`, `reward`, `punish`
* `mental`: `resolve`, `plan`, `realize`, `hesitate`
* `existential`: `cast`, `transform`, `die`, `revive`

**Status Codes**:
- `attempt`: Initiated but result unknown.
- `success`: Goal achieved.
- `failure`: Blocked or ineffective.
- `interrupted`: Stopped by external force.
Optional (only if clearly supported): `backfire`, `partial`.
"""

TARGET_LOGIC = """
### 5. Agents & Targets Logic
* **Agents**: The "Doer" of the event. Must be from the character list if applicable.
* **Targets**: The "Receiver". Can be a `character` or an `object`.

**If Target is an Object, classify `object_type`**:
1. `normal_object`: Standard items.
2. `magical_agent`: Item with agency/personality but not a full character.
3. `price`: The ultimate goal/prize of the hero's quest (e.g., The Golden Apple).
"""

NARRATIVE_FUNCTION_GUIDE = """
### 6. Narrative Function (Optional)
In v3, narrative function is stored in `action_layer.function`.
Set `action_layer.function` to one of these codes if it fits; otherwise use empty string "":
- `trigger`, `climax`, `resolution`, `character_arc`, `setup`, `exposition`
"""

RELATIONSHIPS_V3_GUIDE = """
### 7. Relationships (v3)
In v3, relationships are stored in `relationships`.

- If `target_type` is `object`, set `relationships` to an empty list [].
- If `target_type` is `character`, set `relationships` to a list of relationship entries.
    Each entry MUST be:
    {agent, target, relationship_level1, relationship_level2, sentiment}

Multi-agent/target rule:
- If there are multiple agents and/or multiple targets, include ALL salient pairs explicitly as separate entries.
- If there is exactly one agent and one target, include a single entry.

Output English-only relationship codes (e.g., `parent_child`, `enemy`, etc.).
"""

SYSTEM_PROMPT_NARRATIVE = """You are an expert narrative analyst. Your task is to annotate a specific narrative event within a story segment based on strict structural and taxonomy guidelines.
You must output STRICT JSON only (no markdown, no commentary).
"""

def build_narrative_user_prompt(
    *,
    narrative_id: str,
    text_span: Dict[str, Any],
    narrative_text: str,
    character_list: List[str],
    culture: Optional[str] = None,
    existing_event: Optional[Dict[str, Any]] = None,
    history_events: Optional[List[Dict[str, Any]]] = None,
    mode: Literal["supplement", "modify", "recreate"] = "recreate",
    additional_prompt: Optional[str] = None,
) -> str:
    """Build the user prompt for narrative event annotation.

    Args:
        narrative_id: The ID for this narrative event.
        text_span: The text span information {start, end, text}.
        narrative_text: The full narrative text providing context.
        character_list: List of available character names.
        culture: Optional culture hint.
        existing_event: Optional existing event annotation to use as base.
        history_events: Optional list of previous events for context.
        mode: Annotation mode ("supplement", "modify", or "recreate").
        additional_prompt: Optional additional instructions from the user.
    """

    culture_hint = f"Culture hint: {culture}\n" if culture else ""
    
    # Build mode-specific instructions
    mode_instructions = ""
    if existing_event is not None and mode != "recreate":
        existing_json_str = json.dumps(existing_event, ensure_ascii=False, indent=2)
        if mode == "supplement":
            mode_instructions = (
                "\nIMPORTANT: You have been provided with an existing event annotation. "
                "Your task is to SUPPLEMENT it by filling in ONLY missing fields or empty strings. "
                "DO NOT modify or remove existing filled values. "
                "Keep all existing data as is, and only add detail where it is currently lacking.\n\n"
                "Existing event annotation:\n"
                "---\n"
                f"{existing_json_str}\n"
                "---\n\n"
            )
        elif mode == "modify":
            mode_instructions = (
                "\nIMPORTANT: You have been provided with an existing event annotation. "
                "Your task is to MODIFY and IMPROVE it. "
                "You can fix errors, refine the description, and ensure better alignment with the guidelines. "
                "You should review the existing annotation and enhance it based on the text.\n\n"
                "Existing event annotation:\n"
                "---\n"
                f"{existing_json_str}\n"
                "---\n\n"
            )

    history_context = ""
    if history_events:
        history_json_str = json.dumps(history_events, ensure_ascii=False, indent=2)
        history_context = (
            "\n### PREVIOUS EVENTS CONTEXT\n"
            "Below are the events that occurred earlier in the story. Use these for consistency "
            "(e.g., maintaining character relationships or plot continuity).\n"
            "---\n"
            f"{history_json_str}\n"
            "---\n\n"
        )

    span_str = json.dumps(text_span, ensure_ascii=False)
    char_list_str = json.dumps(character_list, ensure_ascii=False)

    return (
        mode_instructions +
        f"# INPUT DATA\n"
        f"**Narrative ID**: {narrative_id}\n"
        f"**Character List**: {char_list_str}\n"
        f"**Target Text Span**: {span_str}\n\n"
        f"**Full Narrative Text**:\n"
        f"\"{narrative_text}\"\n\n"
        f"{history_context}"
        "---"
        "\n# ANNOTATION GUIDELINES\n"
        f"{PROPP_GUIDE}\n"
        f"{ACTION_GUIDE}\n"
        f"{RELATIONSHIP_GUIDE}\n"
        f"{SENTIMENT_GUIDE}\n"
        f"{TARGET_LOGIC}\n"
        f"{NARRATIVE_FUNCTION_GUIDE}\n"
        f"{RELATIONSHIPS_V3_GUIDE}\n"
        "---\n\n"
        "# DESCRIPTION REQUIREMENTS\n"
        "Provide a `description` field containing two versions separated by a semicolon (;):\n"
        "1. **General/Archetypal**: Abstract summary (e.g., \"Monster kills hero's kin\").\n"
        "2. **Specific**: Details from the text (e.g., \"The Wolf eats grandmother\").\n\n"
        "# OUTPUT FORMAT\n"
        "Return a single Valid JSON object. Do not include markdown formatting.\n\n"
        "**JSON Schema**:\n"
        "{\n"
        f"    \"id\": \"{narrative_id}\",\n"
        f"    \"text_span\": {span_str},\n"
        "    \"event_type\": \"String (Propp Symbol, e.g., 'A' or 'H'; or 'OTHER')\",\n"
        "    \"description\": \"String (General;Specific)\",\n"
        "    \"agents\": [\"String (Name from character list)\"],\n"
        "    \"targets\": [\"String (Name or Object Name)\"],\n"
        "    \"target_type\": \"String ('character' or 'object')\",\n"
        "    \"object_type\": \"String (Only if target_type is object: 'normal_object', 'magical_agent', or 'price'. Else empty string)\",\n"
        "    \"instrument\": \"String (Optional tool used by agent, else empty string)\",\n"
        "    \"relationships\": [\n"
        "      {\n"
        "        \"agent\": \"String (Name from agents)\",\n"
        "        \"target\": \"String (Name from targets)\",\n"
        "        \"relationship_level1\": \"String (Relationship code; English only)\",\n"
        "        \"relationship_level2\": \"String (Relationship code; English only)\",\n"
        "        \"sentiment\": \"String (Sentiment code)\"\n"
        "      }\n"
        "    ],\n"
        "    \"action_layer\": {\n"
        "      \"category\": \"String (physical/communicative/transaction/mental/existential)\",\n"
        "      \"type\": \"String (Action type code under the chosen category)\",\n"
        "      \"context\": \"String (Optional context tag, else empty string)\",\n"
        "      \"status\": \"String (attempt/success/failure/interrupted; optional backfire/partial)\",\n"
        "      \"function\": \"String (Optional narrative function code, else empty string)\"\n"
        "    },\n"
        "    \"time_order\": integer\n"
        "}\n\n"
        f"{culture_hint}"
        + ("" if mode == "recreate" else f"\nRemember: Mode is '{mode}'. Follow the instructions above.\n")
        + (f"\n\nAdditional instructions from user:\n{additional_prompt}\n" if additional_prompt and additional_prompt.strip() else "")
    )

# ==========================================
# Example Usage
# ==========================================
if __name__ == "__main__":
    sample_id = "05828210-380c-4e6f-936c-d5164c1524f6"
    sample_text = "The Cowherd stole the Weaver Girl's heavenly clothes while she was bathing. She could not return to heaven."
    sample_span = {"start": 0, "end": 105, "text": "The Cowherd stole the Weaver Girl's heavenly clothes..."}
    sample_chars = ["Cowherd", "Weaver Girl", "Ox"]
    
    # Generate the prompt in 'recreate' mode
    final_prompt = build_narrative_user_prompt(
        narrative_id=sample_id,
        text_span=sample_span,
        narrative_text=sample_text,
        character_list=sample_chars,
        mode="recreate"
    )
    
    print("--- RECREATE MODE PROMPT ---")
    print(final_prompt)
    print("\n" + "="*50 + "\n")

    # Generate the prompt in 'modify' mode
    existing = {
        "id": sample_id,
        "event_type": "A",
        "description": "Villainy;Cowherd steals clothes",
        "agents": ["Cowherd"],
        "targets": ["clothes"],
        "target_type": "object"
    }
    modify_prompt = build_narrative_user_prompt(
        narrative_id=sample_id,
        text_span=sample_span,
        narrative_text=sample_text,
        character_list=sample_chars,
        existing_event=existing,
        mode="modify"
    )
    print("--- MODIFY MODE PROMPT ---")
    print(modify_prompt)