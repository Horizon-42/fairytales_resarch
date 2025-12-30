import json

class NarrativePromptGenerator:
    def __init__(self):
        self._init_guidelines()

    def _init_guidelines(self):
        """
        Initializes the static guidelines derived from the provided resource files.
        Translated from Chinese to English where necessary.
        """
        
        # Source: propp_functions_guide_en.md
        self.propp_guide = """
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

        # Source: relationship.csv (Translated)
        self.relationship_guide = """
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

        # Source: sentiment.csv (Translated)
        self.sentiment_guide = """
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

        # Source: Universal_Narrative_Action_Taxonomy.md
        self.action_guide = """
        ### 4. Action Category (Universal Taxonomy)
        Mandatory field. Select the most appropriate Category and Type.
        
        * **I. Physical & Conflict**: `attack`, `defend`, `restrain`, `flee`, `steal`, `travel`
        * **II. Communicative & Social**: `inform`, `persuade`, `deceive`, `command`, `slander`, `promise`
        * **III. Transaction & Exchange**: `give`, `request`, `exchange`, `reward`, `punish`, `sacrifice`
        * **IV. Mental & Cognitive**: `observe`, `realize`, `investigate`, `plot`, `forget`
        * **V. Existential & Magical**: `transform`, `cast_spell`, `express_emotion`, `die`, `revive`
        
        **Status Codes**:
        - `attempt`: Initiated but result unknown.
        - `success`: Goal achieved.
        - `failure`: Blocked or ineffective.
        - `interrupted`: Stopped by external force.
        """

        # Source: Narrative标注Prompt草案.md (Target Types)
        self.target_logic = """
        ### 5. Agents & Targets Logic
        * **Agents**: The "Doer" of the event. Must be from the character list if applicable.
        * **Targets**: The "Receiver". Can be a `character` or an `object`.
        
        **If Target is an Object, classify `object_type`**:
        1. `normal_object`: Standard items.
        2. `magical_agent`: Item with agency/personality but not a full character.
        3. `price`: The ultimate goal/prize of the hero's quest (e.g., The Golden Apple).
        """

    def generate_prompt(self, narrative_id, text_span, narrative_text, character_list):
        """
        Generates the full prompt string.
        """
        
        # Convert text_span dict to string representation for the prompt
        span_str = json.dumps(text_span)
        char_list_str = json.dumps(character_list, ensure_ascii=False)

        prompt = f"""
You are an expert narrative analyst. Your task is to annotate a specific narrative event within a story segment based on strict structural and taxonomy guidelines.

# INPUT DATA
**Narrative ID**: {narrative_id}
**Character List**: {char_list_str}
**Target Text Span**: {span_str}

**Full Narrative Text**:
"{narrative_text}"

---

# ANNOTATION GUIDELINES

{self.propp_guide}

{self.action_guide}

{self.relationship_guide}

{self.sentiment_guide}

{self.target_logic}

---

# DESCRIPTION REQUIREMENTS
Provide a `description` field containing two versions separated by a semicolon (;):
1. **General/Archetypal**: Abstract summary (e.g., "Monster kills hero's kin").
2. **Specific**: Details from the text (e.g., "The Wolf eats Little Red Riding Hood's grandmother").

# OUTPUT FORMAT
Return a single Valid JSON object. Do not include markdown formatting (like ```json).

**JSON Schema**:
{{
    "id": "{narrative_id}",
    "text_span": {span_str},
    "event_type": "String (Propp Symbol, e.g., 'A' or 'H')",
    "description": "String (General;Specific)",
    "agents": ["String (Name from character list)"],
    "targets": ["String (Name or Object Name)"],
    "target_type": "String ('character' or 'object')",
    "object_type": "String (Only if target_type is object: 'normal_object', 'magical_agent', or 'price'. Else empty string)",
    "instrument": "String (Optional tool used by agent, else empty string)",
    "relationship_level1": "String (From Relationship Guide, if target is character)",
    "relationship_level2": "String (From Relationship Guide, if target is character)",
    "sentiment": "String (From Sentiment Guide)",
    "action_category": "String (From Action Guide, e.g., 'physical')",
    "action_type": "String (From Action Guide, e.g., 'attack')",
    "action_context": "String (Context keyword from taxonomy, e.g., 'ambush')",
    "action_status": "String ('attempt', 'success', 'failure', 'interrupted')",
    "time_order": 1
}}
"""
        return prompt

# ==========================================
# Example Usage
# ==========================================
if __name__ == "__main__":
    # Mock Data based on the user's example
    generator = NarrativePromptGenerator()
    
    sample_id = "05828210-380c-4e6f-936c-d5164c1524f6"
    sample_text = "The Cowherd stole the Weaver Girl's heavenly clothes while she was bathing. She could not return to heaven."
    sample_span = {"start": 0, "end": 105, "text": "The Cowherd stole the Weaver Girl's heavenly clothes..."}
    sample_chars = ["Cowherd", "Weaver Girl", "Ox"]
    
    # Generate the prompt
    final_prompt = generator.generate_prompt(
        narrative_id=sample_id,
        text_span=sample_span,
        narrative_text=sample_text,
        character_list=sample_chars
    )
    
    print(final_prompt)