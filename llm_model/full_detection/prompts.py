"""Prompt templates for the full detection pipeline."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


# Step 1: Summary
SYSTEM_PROMPT_SUMMARY = """You are an expert folktale analysis assistant.
Your task is to create concise summaries of story segments that preserve key information."""

def build_summary_prompt(text_span: str, story_context: Optional[str] = None) -> str:
    """Build prompt for story segment summary.
    
    Args:
        text_span: The story segment text to summarize
        story_context: Optional full story context
        
    Returns:
        Prompt string
    """
    context_part = ""
    if story_context:
        context_part = f"\n\nFull Story Context:\n{story_context}\n"
    
    return f"""Summarize the following story segment in 4-7 sentences.
Keep key characters and main plot points.
Focus on what happens in this specific segment.

Story Segment:
{text_span}
{context_part}
Output a concise summary (4-7 sentences) that captures the essential narrative elements."""


# Step 2: Character Recognition
SYSTEM_PROMPT_CHARACTER_RECOGNITION = """You are an expert folktale annotation assistant.
Your task is to identify characters and items (entities) in story segments, classifying them as doers (agents) or receivers (targets)."""

def build_character_recognition_prompt(
    text_span: str,
    summary: str,
    existing_characters: List[Dict[str, Any]],
    story_context: Optional[str] = None
) -> str:
    """Build prompt for character recognition.
    
    Args:
        text_span: Story segment text
        summary: Summary from Step 1
        existing_characters: Existing global character list
        story_context: Optional full story context
        
    Returns:
        Prompt string
    """
    context_part = ""
    if story_context:
        context_part = f"\n\nFull Story Context:\n{story_context}\n"
    
    chars_str = ""
    if existing_characters:
        chars_str = "\nExisting Characters:\n"
        for char in existing_characters:
            name = char.get("name", "")
            alias = char.get("alias", "")
            if alias:
                chars_str += f"- {name} (aliases: {alias})\n"
            else:
                chars_str += f"- {name}\n"
    
    return f"""Identify all main characters and items in the following story segment.
Classify each as either a DOER (performs actions) or RECEIVER (receives actions).
Some entities can be both doers and receivers.

Story Segment:
{text_span}

Summary:
{summary}
{chars_str}
{context_part}
Output JSON with the following structure:
{{
  "doers": ["list", "of", "character/item", "names"],
  "receivers": ["list", "of", "character/item", "names"],
  "new_characters": [
    {{"name": "name", "alias": "alias1;alias2", "archetype": "Hero"}},
    ...
  ],
  "notes": "Any notes about alias resolution or character matching"
}}

Important:
- If a character already exists (by name or alias), do NOT add it to new_characters
- Use existing character names when matching
- Items can be objects, magical agents, or prices
- Be careful to resolve aliases correctly (e.g., "孩子" might already be in list as "一儿一女")
"""


# Step 2.5: Instrument Recognition (optional)
SYSTEM_PROMPT_INSTRUMENT = """You are an expert folktale analysis assistant.
Your task is to identify key instruments or tools used by characters in actions."""

def build_instrument_prompt(
    text_span: str,
    summary: str,
    doers: List[str]
) -> str:
    """Build prompt for instrument recognition.
    
    Args:
        text_span: Story segment text
        summary: Summary from Step 1
        doers: List of doer names from Step 2
        
    Returns:
        Prompt string
    """
    doers_str = ", ".join(doers) if doers else "unknown characters"
    
    return f"""Identify if any key instruments or tools are used in this action.
Only identify significant instruments (e.g., magical items, special weapons).
Ignore common or everyday tools.

Story Segment:
{text_span}

Summary:
{summary}

Doers: {doers_str}

Output JSON:
{{
  "instrument": "name of instrument or empty string if none",
  "explanation": "brief explanation"
}}"""


# Step 3: Relationship Deduction
SYSTEM_PROMPT_RELATIONSHIP = """You are an expert folktale annotation assistant.
Your task is to deduce relationships between characters based on narrative context."""

def build_relationship_prompt(
    text_span: str,
    summary: str,
    doers: List[str],
    receivers: List[str],
    story_context: Optional[str] = None
) -> str:
    """Build prompt for relationship deduction.
    
    Args:
        text_span: Story segment text
        summary: Summary from Step 1
        doers: List of doer names
        receivers: List of receiver names (characters only)
        story_context: Optional full story context
        
    Returns:
        Prompt string
    """
    context_part = ""
    if story_context:
        context_part = f"\n\nFull Story Context:\n{story_context}\n"
    
    relationship_guide = """
Relationship Categories (MUST select from these exact options):
- Family & Kinship: parent_child, sibling, spouse, extended_family
- Romance: lover
- Hierarchy: ruler_subject, master_servant, mentor_student, commander_subordinate
- Social & Alliance: friend, ally, colleague
- Adversarial: enemy, rival
- Neutral: stranger

CRITICAL: 
- relationship_level1 MUST be exactly one of: "Family & Kinship", "Romance", "Hierarchy", "Social & Alliance", "Adversarial", "Neutral"
- relationship_level2 MUST be from the corresponding level1 options (e.g., if level1 is "Family & Kinship", level2 must be one of: parent_child, sibling, spouse, extended_family)
- Do NOT invent new relationship types

Sentiment (select one):
- romantic (high positive), positive (friendly), neutral (indifferent)
- negative (dislike), fearful (submissive), hostile (high negative)
"""
    
    return f"""Deduce the relationships between doers and receivers (if receivers are characters).

Story Segment:
{text_span}

Summary:
{summary}

Doers: {', '.join(doers) if doers else 'None'}
Receivers (characters): {', '.join(receivers) if receivers else 'None'}
{context_part}
{relationship_guide}

Output JSON:
{{
  "relationships": [
    {{
      "agent": "doer name",
      "target": "receiver name",
      "relationship_level1": "exact category name from list above",
      "relationship_level2": "exact type from corresponding category options",
      "sentiment": "one of: romantic, positive, neutral, negative, fearful, hostile"
    }},
    ...
  ]
}}

CRITICAL: 
- relationship_level1 and relationship_level2 MUST use exact strings from the guide above
- If receivers are not characters (are objects), return empty relationships array []
- Multiple relationships possible if there are multiple doer-receiver pairs
"""


# Step 4: Action Category Deduction
SYSTEM_PROMPT_ACTION = """You are an expert folktale annotation assistant.
Your task is to classify narrative actions using the Universal Narrative Action Taxonomy."""

def build_action_category_prompt(
    text_span: str,
    summary: str,
    doers: List[str],
    receivers: List[str],
    instrument: str = ""
) -> str:
    """Build prompt for action category deduction.
    
    Args:
        text_span: Story segment text
        summary: Summary from Step 1
        doers: List of doer names
        receivers: List of receiver names
        instrument: Instrument name (if any)
        
    Returns:
        Prompt string
    """
    action_guide = """
Action Categories (MUST select exactly one):
- physical: attack, defend, restrain, flee, travel, interact, steal
- communicative: inform, persuade, deceive, challenge, command, betray, reconcile, slander, promise
- transaction: give, acquire, exchange, reward, punish, request, sacrifice
- mental: resolve, plan, realize, hesitate, observe, investigate, plot, forget
- existential: cast, transform, die, revive, cast_spell, express_emotion

CRITICAL CONSTRAINTS:
- category MUST be exactly one of: "physical", "communicative", "transaction", "mental", "existential"
- type MUST be selected from the corresponding category's options above (e.g., if category is "physical", type must be one of: attack, defend, restrain, flee, travel, interact, steal)
- Do NOT invent new action types - use only the exact codes listed above
- context can be freely generated or left empty, but prefer using recommended tags when applicable

Status (select one):
- attempt, success, failure, interrupted, backfire, partial

Function (narrative role, or empty string):
- trigger, climax, resolution, character_arc, setup, exposition, or empty string
"""
    
    instrument_part = f"\nInstrument used: {instrument}\n" if instrument else ""
    
    return f"""Classify the action in this segment using the Universal Narrative Action Taxonomy.

Story Segment:
{text_span}

Summary:
{summary}

Doers: {', '.join(doers) if doers else 'None'}
Receivers: {', '.join(receivers) if receivers else 'None'}
{instrument_part}
{action_guide}

Output JSON:
{{
  "category": "exact category code from: physical, communicative, transaction, mental, existential",
  "type": "exact action type from the selected category's options (see guide above)",
  "context": "context tag or empty string (can generate freely, but prefer recommended tags)",
  "status": "one of: attempt, success, failure, interrupted, backfire, partial",
  "function": "one of: trigger, climax, resolution, character_arc, setup, exposition, or empty string"
}}

CRITICAL:
- category and type MUST use exact codes from the guide - do NOT invent new codes
- type MUST match the selected category (e.g., if category="physical", type must be one of its options)
- If unsure, check the category's allowed types in the guide above"""


# Step 5: STAC Analysis (we'll reuse the existing STAC analyzer, but provide a prompt template here)
SYSTEM_PROMPT_STAC = """You are an expert narrative analysis assistant.
Your task is to classify sentences into STAC categories and extract relevant information."""

# Note: We'll integrate with existing stac_analyzer module, so this is just for reference
def build_stac_prompt(
    text_span: str,
    summary: str,
    story_context: Optional[str] = None
) -> str:
    """Build prompt for STAC analysis.
    
    Note: This is a reference implementation. We'll integrate with the existing
    stac_analyzer module instead of using this directly.
    """
    context_part = ""
    if story_context:
        context_part = f"\n\nFull Story Context:\n{story_context}\n"
    
    return f"""Analyze this story segment using STAC classification (Situation, Task, Action, Consequence).

Story Segment:
{text_span}

Summary:
{summary}
{context_part}

For each STAC component, provide a one-sentence summary:
- Situation: Background context or setting
- Task: Requirement or responsibility to fulfill
- Action: Activity actively performed
- Consequence: Outcome that changes state

Output JSON:
{{
  "situation": "one sentence",
  "task": "one sentence",
  "action": "one sentence",
  "consequence": "one sentence"
}}"""


# Step 6: Event Type Classification (Propp Functions)
SYSTEM_PROMPT_EVENT_TYPE = """You are an expert folktale analysis assistant.
Your task is to classify narrative events using Vladimir Propp's Morphology of the Folktale."""

PROPP_FUNCTIONS_SUMMARY = """
Key Propp Functions (select one code):
- alpha: Initial Situation (intro of hero/family)
- beta: Absentation (authority leaves)
- gamma: Interdiction (hero warned)
- delta: Violation (rule broken)
- epsilon: Reconnaissance (villain gathers info)
- zeta: Delivery (villain gets info)
- eta: Trickery (villain deceives)
- theta: Complicity (victim submits)
- A: Villainy (villain causes harm) [Driver Type 1]
- a: Lack (family lacks something) [Driver Type 2]
- B: Mediation (hero dispatched)
- C: Counteraction (hero decides)
- arrow_up: Departure (hero leaves)
- D: 1st Function of Donor (hero tested)
- E: Hero's Reaction (responds to test)
- F: Receipt of Agent (acquires magical item)
- G: Guidance (transferred to location)
- H: Struggle (combat with villain)
- J: Branding (hero wounded/marked)
- I: Victory (villain defeated)
- K: Liquidation (lack/villainy resolved)
- arrow_down: Return (hero returns)
- Pr: Pursuit (hero pursued)
- Rs: Rescue (hero rescued)
- o: Unrecognized Arrival (disguised)
- L: Unfounded Claims (false hero claims)
- M: Difficult Task (task proposed)
- N: Solution (task resolved)
- Q: Recognition (hero recognized)
- Ex: Exposure (false hero/villain exposed)
- T: Transfiguration (new appearance/status)
- U: Punishment (villain punished)
- W: Wedding (ultimate reward)
- OTHER: If none fit
"""

def build_event_type_prompt(
    text_span: str,
    summary: str,
    stac: Dict[str, str]
) -> str:
    """Build prompt for event type classification.
    
    Args:
        text_span: Story segment text
        summary: Summary from Step 1
        stac: STAC analysis from Step 5
        
    Returns:
        Prompt string
    """
    stac_str = ""
    if stac:
        stac_str = f"""
STAC Analysis:
- Situation: {stac.get('situation', '')}
- Task: {stac.get('task', '')}
- Action: {stac.get('action', '')}
- Consequence: {stac.get('consequence', '')}
"""
    
    return f"""Classify this event using Vladimir Propp's Morphology of the Folktale.
Focus on the structural role in the narrative, not literal interpretation.

Story Segment:
{text_span}

Summary:
{summary}
{stac_str}
{PROPP_FUNCTIONS_SUMMARY}

Output JSON:
{{
  "event_type": "Propp function code (e.g., 'A', 'a', 'B', or 'OTHER')",
  "description_general": "general description (e.g., 'monster kills hero's family')",
  "description_specific": "specific description (e.g., 'wolf eats Little Red Riding Hood's grandmother')"
}}

Note: If the event fits no specific Propp function, use "OTHER".
Combine the two descriptions with semicolon: "general;specific"
"""
