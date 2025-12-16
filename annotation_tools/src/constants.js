export const ATU_TYPES = [
  "313",
  "402",
  "510A",
  "510B",
  "707",
  "OTHER"
];

export const CHARACTER_ARCHETYPES = [
  "Hero",
  "Shadow",
  "Sidekick",
  "Villain",
  "Lover",
  "Mentor",
  "Mother",
  "Everyman",
  "Damsel",
  "Trickster",
  "Guardian",
  "Herald",
  "Scapegoat",
  "Outlaw",
  "Rebel",
  "Ruler",
  "Other"
];

export const VALUE_TYPES = [
  "CUNNING",
  "LUCK",
  "LOYALTY",
  "COURAGE",
  "OBEDIENCE",
  "DISOBEDIENCE",
  "SACRIFICE",
  "JUSTICE",
  "OTHER"
];

export const ENDING_TYPES = [
  "HAPPY_REUNION",
  "HAPPY_ENDING",
  "BITTERSWEET",
  "TRAGIC",
  "OPEN_ENDED",
  "CLIFFHANGER",
  "CIRCULAR",
  "OTHER"
];

export const PROPP_FUNCTIONS = [
  "ABSENTATION",
  "INTERDICTION",
  "VIOLATION",
  "RECONNAISSANCE",
  "DELIVERY",
  "TRICKERY",
  "COMPLICITY",
  "VILLAINY",
  "LACK",
  "MEDIATION",
  "BEGINNING_COUNTERACTION",
  "DEPARTURE",
  "FIRST_FUNCTION_DONOR",
  "HERO_REACTION",
  "RECEIPT_OF_AGENT",
  "GUIDANCE",
  "STRUGGLE",
  "BRANDING",
  "VICTORY",
  "LIQUIDATION",
  "RETURN",
  "PURSUIT",
  "RESCUE",
  "UNRECOGNIZED_ARRIVAL",
  "UNFOUNDED_CLAIMS",
  "DIFFICULT_TASK",
  "SOLUTION",
  "RECOGNITION",
  "EXPOSURE",
  "TRANSFIGURATION",
  "PUNISHMENT",
  "WEDDING"
];

export const TARGET_CATEGORIES = [
  "character",
  "object"
];

export const OBJECT_TYPES = [
  "normal_object",
  "magical_agent",
  "prize"
];

// Helper Types based on HelperType.md
export const HELPER_TYPES = [
  "ANIMAL",
  "SUPERNATURAL",
  "COMPANION",
  "DEAD",
  "MAIDEN",
  "HUMAN",
  "OBJECT"
];

// Helper type display names mapping
export const HELPER_TYPE_DISPLAY_NAMES = {
  "ANIMAL": "Animal - The Helpful Animal",
  "SUPERNATURAL": "Supernatural - Supernatural Being",
  "COMPANION": "Companion - Extraordinary Companion",
  "DEAD": "Dead - The Grateful Dead",
  "MAIDEN": "Maiden - The Helper Maiden",
  "HUMAN": "Human - The Human Helper",
  "OBJECT": "Object - Magic Object (Active)"
};

// Motif Categories based on Motifs.csv
// Structure: { code: string, category: string, subcategories: Array<{range: string, description: string}> }
export const MOTIF_CATEGORIES = [
  {
    code: "A",
    category: "Mythological",
    subcategories: [
      { range: "A0 - A99", description: "Creator" },
      { range: "A100 - A499", description: "The Gods (Deeds, wars, families of gods)" },
      { range: "A500 - A599", description: "Demigods and Culture Heroes" },
      { range: "A600 - A899", description: "Cosmology (Origin of sky, earth, stars)" },
      { range: "A1200 - A1699", description: "Creation of Man" },
      { range: "A2200 - A2599", description: "Animal Characteristics (Origins of animal traits)" }
    ]
  },
  {
    code: "B",
    category: "Animals",
    subcategories: [
      { range: "B0 - B99", description: "Mythical Animals (Dragons, unicorns, etc.)" },
      { range: "B100 - B199", description: "Magic Animals" },
      { range: "B300 - B599", description: "Friendly Animals (Helpful animals)" },
      { range: "B600 - B699", description: "Marriage to Animals" }
    ]
  },
  {
    code: "C",
    category: "Tabu",
    subcategories: [
      { range: "C0 - C99", description: "Tabu connected with supernatural beings" },
      { range: "C100 - C199", description: "Sex Tabu" },
      { range: "C200 - C299", description: "Eating and Drinking Tabu" },
      { range: "C300 - C399", description: "Looking Tabu (e.g., looking back, looking at secrets)" },
      { range: "C400 - C499", description: "Speaking Tabu (e.g., naming taboos)" }
    ]
  },
  {
    code: "D",
    category: "Magic",
    subcategories: [
      { range: "D0 - D699", description: "Transformation" },
      { range: "D800 - D1699", description: "Magic Objects" },
      { range: "D1700 - D2199", description: "Magic Powers (Flight, invisibility, etc.)" }
    ]
  },
  {
    code: "E",
    category: "The Dead",
    subcategories: [
      { range: "E0 - E199", description: "Resuscitation" },
      { range: "E200 - E599", description: "Ghosts and other Revenants" },
      { range: "E600 - E699", description: "Reincarnation" },
      { range: "E700 - E799", description: "The Soul" }
    ]
  },
  {
    code: "F",
    category: "Marvels",
    subcategories: [
      { range: "F0 - F199", description: "Otherworld Journeys" },
      { range: "F200 - F399", description: "Marvelous Creatures (Fairies, elves, spirits)" },
      { range: "F500 - F599", description: "Remarkable Persons (Monstrous or abnormal physical features)" },
      { range: "F600 - F699", description: "Extraordinary Skill (Companions with super powers)" }
    ]
  },
  {
    code: "G",
    category: "Ogres",
    subcategories: [
      { range: "G10 - G99", description: "Cannibals and Ogres" },
      { range: "G100 - G199", description: "Giant Ogres (Cyclops, etc.)" },
      { range: "G200 - G299", description: "Witches" },
      { range: "G300 - G399", description: "Other Ogres (Goblins, water-monsters)" }
    ]
  },
  {
    code: "H",
    category: "Tests",
    subcategories: [
      { range: "H0 - H199", description: "Identity Tests (Recognition)" },
      { range: "H300 - H499", description: "Marriage Tests" },
      { range: "H500 - H899", description: "Tests of Cleverness (Riddles)" },
      { range: "H900 - H1199", description: "Assignment of Tasks" },
      { range: "H1200 - H1399", description: "Quests" }
    ]
  },
  {
    code: "J",
    category: "The Wise and the Foolish",
    subcategories: [
      { range: "J10 - J100", description: "Acquisition of Wisdom" },
      { range: "J1100 - J1699", description: "Cleverness (Clever acts and words)" },
      { range: "J1700 - J2799", description: "Fools (Numbskulls)" }
    ]
  },
  {
    code: "K",
    category: "Deceptions",
    subcategories: [
      { range: "K0 - K99", description: "Contests won by deception" },
      { range: "K300 - K499", description: "Thefts and Cheats" },
      { range: "K500 - K699", description: "Escape by Deception" },
      { range: "K1300 - K1399", description: "Seduction (or deceptive marriage)" },
      { range: "K1800 - K1899", description: "Deception by Disguise" }
    ]
  },
  {
    code: "L",
    category: "Reversal of Fortune",
    subcategories: [
      { range: "L100 - L199", description: "Unpromising Hero (e.g., youngest son)" },
      { range: "L300 - L399", description: "Triumph of the Weak" },
      { range: "L400 - L499", description: "Pride brought low" }
    ]
  },
  {
    code: "M",
    category: "Ordaining the Future",
    subcategories: [
      { range: "M100 - M199", description: "Vows and Oaths" },
      { range: "M200 - M299", description: "Bargains and Promises" },
      { range: "M300 - M399", description: "Prophecies" },
      { range: "M400 - M499", description: "Curses" }
    ]
  },
  {
    code: "N",
    category: "Chance and Fate",
    subcategories: [
      { range: "N100 - N299", description: "The Nature of Luck (Gambling, etc.)" },
      { range: "N400 - N699", description: "Lucky Accidents" },
      { range: "N800 - N899", description: "Helpers" }
    ]
  },
  {
    code: "P",
    category: "Society",
    subcategories: [
      { range: "P10 - P99", description: "Kings and Princes" },
      { range: "P200 - P299", description: "The Family" }
    ]
  },
  {
    code: "Q",
    category: "Rewards and Punishments",
    subcategories: [
      { range: "Q10 - Q99", description: "Deeds Rewarded" },
      { range: "Q200 - Q399", description: "Deeds Punished" },
      { range: "Q400 - Q599", description: "Kinds of Punishment" }
    ]
  },
  {
    code: "R",
    category: "Captives and Fugitives",
    subcategories: [
      { range: "R10 - R99", description: "Abduction and Captivity" },
      { range: "R100 - R199", description: "Rescues" },
      { range: "R200 - R299", description: "Escapes and Pursuits" }
    ]
  },
  {
    code: "S",
    category: "Unnatural Cruelty",
    subcategories: [
      { range: "S10 - S99", description: "Cruel Parents" },
      { range: "S100 - S199", description: "Revolting Murders" },
      { range: "S200 - S299", description: "Cruel Sacrifices" }
    ]
  },
  {
    code: "T",
    category: "Sex",
    subcategories: [
      { range: "T10 - T99", description: "Love" },
      { range: "T100 - T199", description: "Marriage" },
      { range: "T200 - T299", description: "Married Life" },
      { range: "T500 - T599", description: "Conception and Birth" }
    ]
  },
  {
    code: "V",
    category: "Religion",
    subcategories: [
      { range: "V0 - V99", description: "Religious Services" },
      { range: "V300 - V399", description: "Religious Beliefs" }
    ]
  },
  {
    code: "W",
    category: "Traits of Character",
    subcategories: [
      { range: "W10 - W99", description: "Favorable Traits" },
      { range: "W100 - W199", description: "Unfavorable Traits" }
    ]
  },
  {
    code: "X",
    category: "Humor",
    subcategories: [
      { range: "X900 - X1899", description: "Humor of Lies and Exaggerations" }
    ]
  },
  {
    code: "Z",
    category: "Miscellaneous",
    subcategories: [
      { range: "Z0 - Z99", description: "Formulas" },
      { range: "Z100 - Z199", description: "Symbolism" }
    ]
  }
];
