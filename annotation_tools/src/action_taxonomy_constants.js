// Action Taxonomy constants
// Based on Universal Narrative Action Taxonomy

// Level 1: Action Categories
export const ACTION_CATEGORIES = [
  { code: "physical", name: "Physical & Conflict" },
  // Code kept as "communicative" for backward compatibility (legacy JSON may use it)
  { code: "communicative", name: "Social & Communicative" },
  { code: "transaction", name: "Transaction & Exchange" },
  { code: "mental", name: "Mental & Cognitive" },
  // Code kept as "existential" for backward compatibility (legacy JSON may use it)
  { code: "existential", name: "Existential & Supernatural" }
];

// Level 2: Action Types by Category
export const ACTION_TYPES = {
  physical: [
    // Canonical v2 taxonomy
    { code: "attack", name: "Attack", contextTags: ["ambush", "duel", "spar", "brawl", "mass_battle", "magical_blast"] },
    { code: "defend", name: "Defend", contextTags: ["parry", "shield", "dodge", "bracing"] },
    { code: "restrain", name: "Restrain", contextTags: ["bind", "imprison", "pin_down", "arrest", "seal"] },
    { code: "flee", name: "Flee", contextTags: ["panic", "strategic_retreat", "escape", "obstacle_flight"] },
    { code: "travel", name: "Travel", contextTags: ["quest", "quest_journey", "sneak", "chase", "wander", "flight"] },
    { code: "interact", name: "Interact", contextTags: ["consume", "repair", "destroy_obj", "craft"] },

    // Legacy / compatibility: keep old codes selectable so old JSON round-trips
    { code: "steal", name: "Steal", contextTags: ["pickpocket", "heist", "switch"] }
  ],
  communicative: [
    // Canonical v2 taxonomy
    { code: "inform", name: "Inform", contextTags: ["report", "reveal", "explain", "confess", "rumor"] },
    { code: "persuade", name: "Persuade", contextTags: ["advise", "beg", "negotiate", "seduce", "debate"] },
    { code: "deceive", name: "Deceive", contextTags: ["lie", "feign", "disguise", "mislead"] },
    { code: "challenge", name: "Challenge", contextTags: ["provoke", "duel_proposal", "threaten"] },
    { code: "command", name: "Command", contextTags: ["order", "decree", "coerce", "assign_task", "intimidation", "task_assignment"] },
    { code: "betray", name: "Betray", contextTags: ["backstab", "defect", "break_oath"] },
    { code: "reconcile", name: "Reconcile", contextTags: ["apologize", "comfort", "forgive", "mediate"] },

    // Legacy / compatibility
    { code: "slander", name: "Slander", contextTags: ["framing", "court_intrigue", "defamation"] },
    { code: "promise", name: "Promise", contextTags: ["oath", "marriage_proposal", "contract"] }
  ],
  transaction: [
    // Canonical v2 taxonomy
    { code: "give", name: "Give", contextTags: ["gift", "alms", "legacy", "supply", "inheritance"] },
    { code: "acquire", name: "Acquire", contextTags: ["steal", "borrow", "seize", "loot"] },
    { code: "exchange", name: "Exchange", contextTags: ["trade", "barter", "bribe", "buy"] },
    { code: "reward", name: "Reward", contextTags: ["promote", "pay", "honor", "bless", "promotion", "title", "treasure"] },
    { code: "punish", name: "Punish", contextTags: ["fine", "exile", "execution", "demote"] },

    // Legacy / compatibility
    { code: "request", name: "Request", contextTags: ["demand", "pray", "borrow"] },
    { code: "sacrifice", name: "Sacrifice", contextTags: ["self_sacrifice", "offering", "martyrdom"] }
  ],
  mental: [
    // Canonical v2 taxonomy
    { code: "resolve", name: "Resolve", contextTags: ["decide", "vow", "steel_oneself", "harden_heart"] },
    { code: "plan", name: "Plan", contextTags: ["scheme", "strategize", "plot", "strategy"] },
    { code: "realize", name: "Realize", contextTags: ["epiphany", "detect", "deduce", "discovery", "see_through"] },
    { code: "hesitate", name: "Hesitate", contextTags: ["doubt", "fear", "waver", "confuse"] },

    // Legacy / compatibility
    { code: "observe", name: "Observe", contextTags: ["spy", "inspect", "watch"] },
    { code: "investigate", name: "Investigate", contextTags: ["search", "interrogate", "track"] },
    { code: "plot", name: "Plot", contextTags: ["scheme", "strategy", "hesitate"] },
    { code: "forget", name: "Forget", contextTags: ["amnesia", "ignore", "magic_forgetfulness"] }
  ],
  existential: [
    // Canonical v2 taxonomy
    { code: "cast", name: "Cast", contextTags: ["curse", "heal", "summon", "enchant", "bless"] },
    { code: "transform", name: "Transform", contextTags: ["shapeshift", "grow", "shrink", "disguise_reveal", "growth"] },
    { code: "die", name: "Die", contextTags: ["sacrifice", "perish", "murdered", "suicide", "natural_death"] },
    { code: "revive", name: "Revive", contextTags: ["awaken", "resurrect", "regenerate", "resurrection", "reincarnation", "awakening"] },

    // Legacy / compatibility
    { code: "cast_spell", name: "Cast Spell", contextTags: ["curse", "bless", "summon", "heal"] },
    { code: "express_emotion", name: "Express Emotion", contextTags: ["cry", "mourn", "laugh", "rage"] }
  ]
};

// Status codes
export const ACTION_STATUS = [
  { code: "attempt", name: "Attempt" },
  { code: "success", name: "Success" },
  { code: "failure", name: "Failure" },
  { code: "interrupted", name: "Interrupted" },
  // Newer taxonomy tags (kept optional)
  { code: "backfire", name: "Backfire" },
  { code: "partial", name: "Partial" }
];

// Narrative Function layer (optional)
// Default is empty string (unset). Keep options stable and minimal.
// Note: some docs use "exposition" while the bilingual v2.0 doc uses "setup".
// We include both to preserve backward compatibility.
export const NARRATIVE_FUNCTIONS = [
  { code: "trigger", name: "Trigger" },
  { code: "climax", name: "Climax" },
  { code: "resolution", name: "Resolution" },
  { code: "character_arc", name: "Character arc" },
  { code: "setup", name: "Setup" },
  { code: "exposition", name: "Exposition" }
];

// Helper function to get action types for a category
export function getActionTypesForCategory(categoryCode) {
  return ACTION_TYPES[categoryCode] || [];
}

// Helper function to get context tags for an action type
export function getContextTagsForAction(categoryCode, actionCode) {
  const actions = ACTION_TYPES[categoryCode] || [];
  const action = actions.find(a => a.code === actionCode);
  return action ? action.contextTags : [];
}
