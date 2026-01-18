# 故事生成 Prompt 模板

本文档包含从 `generate_stories.py` 提取的故事生成 prompt，可直接在网页聊天中使用。

## Prompt 模板

```
You are a master storyteller with deep expertise in {culture} folktales, myths, and traditional narratives. Your task is to create a complete, engaging story that faithfully follows the provided narrative structure while bringing it to life with rich detail and cultural authenticity.

**CRITICAL LANGUAGE REQUIREMENT:**
You MUST write the entire story in {story_language}. This is not optional. Every word, sentence, and paragraph must be in {story_language}, not English or any other language.

**STORY INFORMATION:**
- Title: {title}
- Cultural Origin: {culture}
- Required Language: {story_language}

**CHARACTERS:**
{character_list}

Each character has an archetypal role. Develop them in a way that is consistent with their archetype while also giving them depth and personality. Use character names consistently throughout the story, including any aliases provided.

**NARRATIVE STRUCTURE:**

The story must follow these {num_events} events in the exact order specified. Each event must correspond to ONE paragraph in your output, wrapped in curly braces {}:

{events_text}

Each event represents a key plot point that must be included in your narrative. The event type (e.g., VILLAINY, DEPARTURE, VICTORY) indicates the narrative function, which should inform how you present and develop that moment in the story. You must generate exactly {num_events} paragraphs, each wrapped in {}, corresponding to these {num_events} events in order.

**STORY GENERATION REQUIREMENTS:**

1. **Narrative Flow**: The story must progress smoothly through all events in chronological order. Create natural transitions between events that feel organic and engaging.

2. **Character Development**: Include all listed characters and develop their roles naturally. Characters should feel authentic to their archetypal roles while also having individual personalities.

3. **Cultural Authenticity**: 
   - Use appropriate cultural details, settings, and traditions for {culture} folktales
   - Incorporate relevant cultural elements, motifs, and storytelling conventions
   - Maintain the traditional narrative style typical of {culture} stories

4. **Writing Style**:
   - Use vivid, descriptive language that brings scenes to life
   - Include sensory details (sights, sounds, emotions) where appropriate
   - Balance dialogue and narration effectively
   - Create tension and emotional resonance where the events suggest it

5. **Completeness**: The story should be self-contained and readable as a standalone narrative. Do not include meta-commentary, explanations, or analysis—only the story itself.

6. **Length**: Generate a substantial, well-developed story that fully explores each event. Aim for a length appropriate to the complexity of the narrative structure provided.

**OUTPUT FORMAT - CRITICAL:**

You must format the story as follows:
- Each narrative event corresponds to ONE story paragraph
- Each paragraph MUST be wrapped in curly braces {}
- The paragraphs must appear in the exact order of the events (Event 1, Event 2, ..., Event {num_events})
- Each paragraph should be a self-contained narrative segment that develops the corresponding event

Format example:
{First paragraph corresponding to Event 1}
{Second paragraph corresponding to Event 2}
{Third paragraph corresponding to Event 3}
...

Requirements:
- Each {} block should contain the story text for ONE narrative event only
- Do NOT include any text outside the curly braces
- Do NOT include the event numbers or labels inside the braces
- Do NOT include any introduction, explanation, meta-commentary, notes, or analysis
- Do NOT include the title
- The story should flow naturally from one {} block to the next

**LANGUAGE REMINDER:**
CRITICAL: You must write the entire story in {story_language}, not in English. The story must be completely in {story_language} from the first word to the last word. Do not use English at all.

**BEGIN THE STORY NOW (with proper formatting):**
```

## 变量说明

在使用上述 prompt 时，需要替换以下变量：

### 必需变量

- **{culture}**: 故事的文化背景（如：Chinese, Japanese, Indian, Persian, English）
- **{story_language}**: 故事的语言（如：中文, English, Japanese, Persian）
- **{title}**: 故事标题
- **{character_list}**: 角色列表，格式如下：
  ```
  - 角色名 (角色类型)
  - 角色名 (角色类型) - also known as: 别名
  ```
  示例：
  ```
  - 牛郎 (Hero)
  - 织女 (Princess) - also known as: 七仙女
  - 王母娘娘 (Villain)
  ```
- **{num_events}**: 事件总数（数字）
- **{events_text}**: 事件列表，每行一个事件，格式如下：
  ```
  Event 1: [事件类型] 事件描述 | Agents: 行动者 | Targets: 目标 | Instrument: 工具
  Event 2: [事件类型] 事件描述 | Agents: 行动者 | Targets: 目标
  Event 3: [事件类型] 事件描述
  ```
  示例：
  ```
  Event 1: [VILLAINY] 王母娘娘阻止牛郎和织女相会 | Agents: 王母娘娘 | Targets: 牛郎, 织女
  Event 2: [DEPARTURE] 牛郎决定寻找织女 | Agents: 牛郎
  Event 3: [VICTORY] 牛郎和织女最终在一起 | Agents: 牛郎, 织女
  ```

## 语言映射

根据文化背景确定故事语言：

- **Chinese** → 中文
- **Japanese** → Japanese
- **Indian** → English
- **Persian** → Persian
- **English** → English

## 使用示例

### 示例 1：中文故事

```
You are a master storyteller with deep expertise in Chinese folktales, myths, and traditional narratives. Your task is to create a complete, engaging story that faithfully follows the provided narrative structure while bringing it to life with rich detail and cultural authenticity.

**CRITICAL LANGUAGE REQUIREMENT:**
You MUST write the entire story in 中文. This is not optional. Every word, sentence, and paragraph must be in 中文, not English or any other language.

**STORY INFORMATION:**
- Title: 牛郎织女
- Cultural Origin: Chinese
- Required Language: 中文

**CHARACTERS:**
- 牛郎 (Hero)
- 织女 (Princess) - also known as: 七仙女
- 王母娘娘 (Villain)

Each character has an archetypal role. Develop them in a way that is consistent with their archetype while also giving them depth and personality. Use character names consistently throughout the story, including any aliases provided.

**NARRATIVE STRUCTURE:**

The story must follow these 3 events in the exact order specified. Each event must correspond to ONE paragraph in your output, wrapped in curly braces {}:

Event 1: [VILLAINY] 王母娘娘阻止牛郎和织女相会 | Agents: 王母娘娘 | Targets: 牛郎, 织女
Event 2: [DEPARTURE] 牛郎决定寻找织女 | Agents: 牛郎
Event 3: [VICTORY] 牛郎和织女最终在一起 | Agents: 牛郎, 织女

Each event represents a key plot point that must be included in your narrative. The event type (e.g., VILLAINY, DEPARTURE, VICTORY) indicates the narrative function, which should inform how you present and develop that moment in the story. You must generate exactly 3 paragraphs, each wrapped in {}, corresponding to these 3 events in order.

**STORY GENERATION REQUIREMENTS:**

1. **Narrative Flow**: The story must progress smoothly through all events in chronological order. Create natural transitions between events that feel organic and engaging.

2. **Character Development**: Include all listed characters and develop their roles naturally. Characters should feel authentic to their archetypal roles while also having individual personalities.

3. **Cultural Authenticity**: 
   - Use appropriate cultural details, settings, and traditions for Chinese folktales
   - Incorporate relevant cultural elements, motifs, and storytelling conventions
   - Maintain the traditional narrative style typical of Chinese stories

4. **Writing Style**:
   - Use vivid, descriptive language that brings scenes to life
   - Include sensory details (sights, sounds, emotions) where appropriate
   - Balance dialogue and narration effectively
   - Create tension and emotional resonance where the events suggest it

5. **Completeness**: The story should be self-contained and readable as a standalone narrative. Do not include meta-commentary, explanations, or analysis—only the story itself.

6. **Length**: Generate a substantial, well-developed story that fully explores each event. Aim for a length appropriate to the complexity of the narrative structure provided.

**OUTPUT FORMAT - CRITICAL:**

You must format the story as follows:
- Each narrative event corresponds to ONE story paragraph
- Each paragraph MUST be wrapped in curly braces {}
- The paragraphs must appear in the exact order of the events (Event 1, Event 2, Event 3)
- Each paragraph should be a self-contained narrative segment that develops the corresponding event

Format example:
{First paragraph corresponding to Event 1}
{Second paragraph corresponding to Event 2}
{Third paragraph corresponding to Event 3}

Requirements:
- Each {} block should contain the story text for ONE narrative event only
- Do NOT include any text outside the curly braces
- Do NOT include the event numbers or labels inside the braces
- Do NOT include any introduction, explanation, meta-commentary, notes, or analysis
- Do NOT include the title
- The story should flow naturally from one {} block to the next

**LANGUAGE REMINDER:**
CRITICAL: You must write the entire story in 中文, not in English. The story must be completely in 中文 from the first word to the last word. Do not use English at all.

**BEGIN THE STORY NOW (with proper formatting):**
```

## 输出格式示例

模型应该返回类似以下格式的故事：

```
{从前，牛郎和织女是一对恩爱的夫妻，他们住在天上的银河边。但是，王母娘娘认为他们的结合违反了天条，于是派天兵天将将他们分开，用银河将他们阻隔。牛郎和织女只能隔河相望，无法团聚。}
{牛郎看着对岸的织女，心中充满了思念和不舍。他决定不顾一切困难，去寻找织女。他骑上老牛，带着两个孩子，踏上了跨越银河的艰难旅程。即使面对王母娘娘的阻挠和银河的险阻，他也绝不放弃。}
{最终，牛郎的真心感动了天地，喜鹊们纷纷飞来，在银河上搭起了一座鹊桥。牛郎和织女终于在鹊桥上相会，他们的爱情战胜了天条和阻隔。虽然每年只能在七夕这一天相会，但他们的爱情却永恒不变，成为了千古传颂的佳话。}
```

## 注意事项

1. **语言一致性**：确保整个故事都使用指定的语言，不要混用英文或其他语言
2. **格式要求**：每个段落必须用 `{}` 包裹，不要有多余的文本
3. **事件顺序**：严格按照提供的事件顺序生成故事段落
4. **文化准确性**：根据文化背景使用相应的文化元素和叙事风格
5. **段落完整性**：每个 `{}` 中的段落应该是一个完整的叙事片段，对应一个事件
