// Sentiment tags
// Generated from Character_Resources/sentiment.csv

export const SENTIMENT_TAGS = [
  "romantic",
  "positive",
  "neutral",
  "negative",
  "fearful",
  "hostile"
];

export const SENTIMENT_DATA = [
  {
    "tag": "romantic",
    "chineseName": "爱慕/迷恋",
    "polarity": "High Positive",
    "behavior": "求爱、性吸引、深情凝视、脸红。"
  },
  {
    "tag": "positive",
    "chineseName": "友好/喜爱",
    "polarity": "Positive",
    "behavior": "信任、感激、尊敬、帮助、赞同。"
  },
  {
    "tag": "neutral",
    "chineseName": "中立/冷漠",
    "polarity": "Neutral",
    "behavior": "商业交易、无情绪的问答、路过。"
  },
  {
    "tag": "negative",
    "chineseName": "厌恶/反感",
    "polarity": "Negative",
    "behavior": "嘲讽、拒绝、不耐烦、轻视、争吵。"
  },
  {
    "tag": "fearful",
    "chineseName": "恐惧/服从",
    "polarity": "Negative (Passive)",
    "behavior": "发抖、求饶、被迫下跪、逃跑。"
  },
  {
    "tag": "hostile",
    "chineseName": "敌对/杀意",
    "polarity": "High Negative",
    "behavior": "攻击、诅咒、愤怒、试图伤害/杀死。"
  }
];

// Helper function to get sentiment by tag
export function getSentimentByTag(tag) {
  return SENTIMENT_DATA.find(s => s.tag === tag);
}
