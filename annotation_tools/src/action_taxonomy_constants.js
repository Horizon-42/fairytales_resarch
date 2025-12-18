// Action Taxonomy constants
// Based on Universal Narrative Action Taxonomy

// Level 1: Action Categories
export const ACTION_CATEGORIES = [
  { code: "physical", name: "Physical & Conflict" },
  { code: "communicative", name: "Communicative & Social" },
  { code: "transaction", name: "Transaction & Exchange" },
  { code: "mental", name: "Mental & Cognitive" },
  { code: "existential", name: "Existential & Magical" }
];

// Level 2: Action Types by Category
export const ACTION_TYPES = {
  physical: [
    { code: "attack", name: "Attack", contextTags: ["ambush", "duel", "mass_battle", "magical_blast"] },
    { code: "defend", name: "Defend", contextTags: ["parry", "shield", "dodge"] },
    { code: "restrain", name: "Restrain", contextTags: ["bind", "imprison", "seal", "arrest"] },
    { code: "flee", name: "Flee", contextTags: ["panic", "strategic_retreat", "obstacle_flight"] },
    { code: "steal", name: "Steal", contextTags: ["pickpocket", "heist", "switch"] },
    { code: "travel", name: "Travel", contextTags: ["quest_journey", "flight", "sneak"] }
  ],
  communicative: [
    { code: "inform", name: "Inform", contextTags: ["report", "rumor", "confess"] },
    { code: "persuade", name: "Persuade", contextTags: ["advise", "beg", "seduce", "debate"] },
    { code: "deceive", name: "Deceive", contextTags: ["disguise", "lie", "feign"] },
    { code: "command", name: "Command", contextTags: ["decree", "intimidation", "task_assignment"] },
    { code: "slander", name: "Slander", contextTags: ["framing", "court_intrigue", "defamation"] },
    { code: "promise", name: "Promise", contextTags: ["oath", "marriage_proposal", "contract"] }
  ],
  transaction: [
    { code: "give", name: "Give", contextTags: ["alms", "gift", "inheritance"] },
    { code: "request", name: "Request", contextTags: ["demand", "pray", "borrow"] },
    { code: "exchange", name: "Exchange", contextTags: ["barter", "buy", "bribe"] },
    { code: "reward", name: "Reward", contextTags: ["promotion", "title", "treasure"] },
    { code: "punish", name: "Punish", contextTags: ["execution", "exile", "fine"] },
    { code: "sacrifice", name: "Sacrifice", contextTags: ["self_sacrifice", "offering", "martyrdom"] }
  ],
  mental: [
    { code: "observe", name: "Observe", contextTags: ["spy", "inspect", "watch"] },
    { code: "realize", name: "Realize", contextTags: ["epiphany", "discovery", "see_through"] },
    { code: "investigate", name: "Investigate", contextTags: ["search", "interrogate", "track"] },
    { code: "plot", name: "Plot", contextTags: ["scheme", "strategy", "hesitate"] },
    { code: "forget", name: "Forget", contextTags: ["amnesia", "ignore", "magic_forgetfulness"] }
  ],
  existential: [
    { code: "transform", name: "Transform", contextTags: ["shapeshift", "disguise_reveal", "growth"] },
    { code: "cast_spell", name: "Cast Spell", contextTags: ["curse", "bless", "summon", "heal"] },
    { code: "express_emotion", name: "Express Emotion", contextTags: ["cry", "mourn", "laugh", "rage"] },
    { code: "die", name: "Die", contextTags: ["suicide", "natural_death", "murdered"] },
    { code: "revive", name: "Revive", contextTags: ["resurrection", "reincarnation", "awakening"] }
  ]
};

// Status codes
export const ACTION_STATUS = [
  { code: "attempt", name: "Attempt" },
  { code: "success", name: "Success" },
  { code: "failure", name: "Failure" },
  { code: "interrupted", name: "Interrupted" }
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
