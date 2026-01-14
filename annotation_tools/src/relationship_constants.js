// Relationship categories with two-level structure
// Generated from Character_Resources/relationship.csv

export const RELATIONSHIP_LEVEL1 = [
  "Family & Kinship",
  "Romance",
  "Hierarchy",
  "Social & Alliance",
  "Adversarial",
  "Neutral"
];

export const RELATIONSHIP_LEVEL2 = {
  "Family & Kinship": [
    {
      "tag": "parent_child",
      "definition": "父母子女垂直的抚养与权威关系（含养父母）。",
      "context": "继母虐待、父王驱逐王子、母亲救子。"
    },
    {
      "tag": "sibling",
      "definition": "兄弟姐妹水平的血缘或结拜关系，常伴随竞争。",
      "context": "兄弟分家、姐姐保护妹妹、该隐与亚伯。"
    },
    {
      "tag": "spouse",
      "definition": "夫妻/配偶法律或习俗认可的长期伴侣（契约性）。",
      "context": "寻找失踪妻子、王后背叛国王。"
    },
    {
      "tag": "extended_family",
      "definition": "亲戚/宗族非直系亲属（叔舅姑姨、祖父母）。",
      "context": "舅舅作为监护人或反派、祖母给予指引。"
    }
  ],
  "Romance": [
    {
      "tag": "lover",
      "definition": "恋人/情人基于激情或追求的非婚姻关系（含婚外情）。",
      "context": "罗密欧与朱丽叶、骑士追求贵妇、初恋。"
    }
  ],
  "Hierarchy": [
    {
      "tag": "ruler_subject",
      "definition": "君臣/领主基于国家、领土或法律的政治统治权。",
      "context": "臣子进谏、国王判决、骑士效忠领主。"
    },
    {
      "tag": "master_servant",
      "definition": "主仆/雇佣基于人身依附、所有权或金钱的支配权。",
      "context": "财主与长工、灯神与阿拉丁、老爷与管家。"
    },
    {
      "tag": "mentor_student",
      "definition": "师徒/导师基于知识、技能或智慧传承的引导关系。",
      "context": "巫师教导学徒、武林宗师传功、智者指路。"
    },
    {
      "tag": "commander_subordinate",
      "definition": "长官/下属基于特定组织（军队/帮派）的指挥链。",
      "context": "将军命令士兵、强盗头子指挥喽啰。"
    }
  ],
  "Social & Alliance": [
    {
      "tag": "friend",
      "definition": "朋友/挚友基于私人情感的亲密连接，无直接功利性。",
      "context": "一起长大的发小、互相信任的旅伴。"
    },
    {
      "tag": "ally",
      "definition": "盟友/伙伴基于共同目标（利益）的临时或长期合作。",
      "context": "敌对两国联合抗龙、临时组队寻宝。"
    },
    {
      "tag": "colleague",
      "definition": "同僚/同门职业平级或师出同门（非血缘）的关系。",
      "context": "一起站岗的卫兵、同一门派的竞争师兄。"
    }
  ],
  "Adversarial": [
    {
      "tag": "enemy",
      "definition": "死敌/仇人核心是毁灭或仇恨，目的是消灭对方。",
      "context": "英雄 vs 魔王、杀父之仇、正邪对立。"
    },
    {
      "tag": "rival",
      "definition": "对手/情敌核心是竞争（争夺荣誉/奖品/爱人），不一定致死。",
      "context": "吹牛比赛对手、追求同一人的两个骑士。"
    }
  ],
  "Neutral": [
    {
      "tag": "stranger",
      "definition": "陌生人此前无任何社会交集。",
      "context": "路人、偶遇的怪兽、旅店过客。"
    }
  ]
};

// Helper function to get level 2 options for a given level 1
export function getRelationshipLevel2Options(level1) {
  return RELATIONSHIP_LEVEL2[level1] || [];
}
