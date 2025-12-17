export const ATU_TYPES = [
  "313",
  "402",
  "510A",
  "510B",
  "707",
  "OTHER"
];

// ATU hierarchical categories based on ATU_types.csv
// Each row corresponds to a range of ATU numbers and a category name.
// level:
//  - 1: top-level group (e.g., ANIMAL TALES)
//  - 2: subgroup
//  - 3: sub-subgroup (most specific)
export const ATU_CATEGORY_ROWS = [
  { start: 1, end: 299, name: "ANIMAL TALES", level: 1 },
  { start: 1, end: 99, name: "Wild Animals", level: 2 },
  { start: 1, end: 69, name: "The Clever Fox (Other Animal)", level: 3 },
  { start: 70, end: 99, name: "Other Wild Animals", level: 3 },
  { start: 100, end: 149, name: "Wild Animals and Domestic Animals", level: 2 },
  { start: 150, end: 199, name: "Wild Animals and Humans", level: 2 },
  { start: 200, end: 219, name: "Domestic Animals", level: 2 },
  { start: 220, end: 299, name: "Other Animals and Objects", level: 2 },

  { start: 300, end: 749, name: "TALES OF MAGIC", level: 1 },
  { start: 300, end: 399, name: "Supernatural Adversaries", level: 2 },
  { start: 400, end: 459, name: "Supernatural or Enchanted Wife (Husband) or Other Relative", level: 2 },
  { start: 400, end: 424, name: "Wife", level: 3 },
  { start: 425, end: 449, name: "Husband", level: 3 },
  { start: 450, end: 459, name: "Brother or Sister", level: 3 },
  { start: 460, end: 499, name: "Supernatural Tasks", level: 2 },
  { start: 500, end: 559, name: "Supernatural Helpers", level: 2 },
  { start: 560, end: 649, name: "Magic Objects", level: 2 },
  { start: 650, end: 699, name: "Supernatural Power or Knowledge", level: 2 },
  { start: 700, end: 749, name: "Other Tales of the Supernatural", level: 2 },

  { start: 750, end: 849, name: "RELIGIOUS TALES", level: 1 },
  { start: 750, end: 779, name: "God Rewards and Punishes", level: 2 },
  { start: 780, end: 799, name: "The Truth Comes to Light", level: 2 },
  { start: 800, end: 809, name: "Heaven", level: 2 },
  { start: 810, end: 826, name: "The Devil", level: 2 },
  { start: 827, end: 849, name: "Other Religious Tales", level: 2 },

  { start: 850, end: 999, name: "REALISTIC TALES", level: 1 },
  { start: 850, end: 869, name: "The Man Marries the Princess", level: 2 },
  { start: 870, end: 879, name: "The Woman Marries the Prince", level: 2 },
  { start: 880, end: 899, name: "Proofs of Fidelity and Innocence", level: 2 },
  { start: 900, end: 909, name: "The Obstinate Wife Learns to Obey", level: 2 },
  { start: 910, end: 919, name: "Good Precepts", level: 2 },
  { start: 920, end: 929, name: "Clever Acts and Words", level: 2 },
  { start: 930, end: 949, name: "Tales of Fate", level: 2 },
  { start: 950, end: 969, name: "Robbers and Murderers", level: 2 },
  { start: 970, end: 999, name: "Other Realistic Tales", level: 2 },

  { start: 1000, end: 1199, name: "TALES OF THE STUPID OGRE (GIANT, DEVIL)", level: 1 },
  { start: 1000, end: 1029, name: "Labor Contract", level: 2 },
  { start: 1030, end: 1059, name: "Partnership between Man and Ogre", level: 2 },
  { start: 1060, end: 1114, name: "Contest between Man and Ogre", level: 2 },
  { start: 1115, end: 1144, name: "Man Kills (Injures) Ogre", level: 2 },
  { start: 1145, end: 1154, name: "Ogre Frightened by Man", level: 2 },
  { start: 1155, end: 1169, name: "Man Outwits the Devil", level: 2 },
  { start: 1170, end: 1199, name: "Souls Saved from the Devil", level: 2 },

  { start: 1200, end: 1999, name: "ANECDOTES AND JOKES", level: 1 },
  { start: 1200, end: 1349, name: "Stories about a Fool", level: 2 },
  { start: 1350, end: 1439, name: "Stories about Married Couples", level: 2 },
  { start: 1380, end: 1404, name: "The Foolish Wife and Her Husband", level: 3 },
  { start: 1405, end: 1429, name: "The Foolish Husband and His Wife", level: 3 },
  { start: 1430, end: 1439, name: "The Foolish Couple", level: 3 },
  { start: 1440, end: 1524, name: "Stories about a Woman", level: 2 },
  { start: 1450, end: 1474, name: "Looking for a Wife", level: 3 },
  { start: 1475, end: 1499, name: "Jokes about Old Maids", level: 3 },
  { start: 1500, end: 1524, name: "Other Stories about Women", level: 3 },
  { start: 1525, end: 1724, name: "Stories about a Man", level: 2 },
  { start: 1525, end: 1639, name: "The Clever Man", level: 3 },
  { start: 1640, end: 1674, name: "Lucky Accidents", level: 3 },
  { start: 1675, end: 1724, name: "The Stupid Man", level: 3 },
  { start: 1725, end: 1849, name: "Jokes about Clergymen and Religious Figures", level: 2 },
  { start: 1725, end: 1774, name: "The Clergyman is Tricked", level: 3 },
  { start: 1775, end: 1799, name: "Clergyman and Sexton", level: 3 },
  { start: 1800, end: 1849, name: "Other Jokes about Religious Figures", level: 3 },
  { start: 1850, end: 1874, name: "Anecdotes about Other Groups of People", level: 2 },
  { start: 1875, end: 1999, name: "Tall Tales", level: 2 },

  { start: 2000, end: 2399, name: "FORMULA TALES", level: 1 },
  { start: 2000, end: 2100, name: "Cumulative Tales", level: 2 },
  { start: 2000, end: 2020, name: "Chains Based on Numbers, Objects, Animals, or Names", level: 3 },
  { start: 2021, end: 2024, name: "Chains Involving Death", level: 3 },
  { start: 2025, end: 2028, name: "Chains Involving Eating", level: 3 },
  { start: 2029, end: 2075, name: "Chains Involving Other Events", level: 3 },
  { start: 2200, end: 2299, name: "Catch Tales", level: 2 },
  { start: 2300, end: 2399, name: "Other Formula Tales", level: 2 }
];

export const CHARACTER_ARCHETYPES = [
  "Hero",
  "Shadow",
  "Sidekick/Helper",
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
