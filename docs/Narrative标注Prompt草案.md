# 输入
0. narrative id
1. Text Selection index, 包括start, end
2. 根据Text Selection 从故事文本中获得相应的narrative文本
3. 角色列表

# Event Type
根据 docs/Propp_Resoruces/propp_functions_guide_en.md 来标注 prop功能; 注意propp是根据俄罗斯故事总结出来的, 所以如果无法选出合适的propp功能，可以直接省略

# Description / Detail
对event的总结性陈述。注意陈述需要有两个版本, 第一个版本是一般性的，如“怪物杀死了英雄的亲人",另一个是具体的，如"狼吃掉了小红帽的外婆"，两个版本之间用；区分.

# Agents and Targets
## Agents (Doer)
从输入的narrative文本中，结合角色列表, 提取出event的doer
Agents可以有多个，注意必须都是doer
## Targets
targets可以有两种类别，
### character
这说明event的Receiver也是角色，直接从角色列表选取
### object
如果Receiver是物品，需要先找出targets（在故事中的称呼），并对其进行分类. 
有三种object_type：
- normal_object
- magical_agent
- price
其中price指的是故事中英雄追求的事物，例如"金苹果”；而magical_agent指的是有角色特性，但是又没有被直接划分为角色的物品
## Instrument
某些动作中，doer用到了特殊的物品作为工具. 这一项是可选的，如果没有或者是很平凡的工具，可以直接忽略

# Relationship
在targets也是角色的情况下, 
根据 docs/Character_Resources/relationship.csv 标注人物关系, 
并根据 docs/Character_Resources/sentiment.csv 标注当前叙事下的情感状态.
注意情感状态跟角色关系可以是独立的甚至是矛盾的，doer可能对处于同盟关系下的target有厌恶情绪，而敌对身份的角色们也能发展浪漫关系(罗密欧与朱丽叶)

# Action Category
在targets也是角色的情况下，
根据 docs/Universal Narrative Action Taxonomy/Universal_Narrative_Action_Taxonomy.md 标注Action Category.
相比propp，Universal Narrative Action Taxonomy是比较一般的，所以是必须标注的，不能略过.

# 结果结构
输出的应该是一个单独的Narrative json 对象，能够方便地插入到整个标注对象中.
```
{
    "event_type": "OTHER",
    "description": "织;neat",
    "agents": [
    "织女"
    ],
    "targets": [
    "天衣"
    ],
    "target_type": "object",
    "object_type": "normal_object",
    "instrument": "",
    "text_span": {
    "start": 0,
    "end": 214,
    "text": "..."
    },
    "id": "05828210-380c-4e6f-936c-d5164c1524f6",
    "time_order": 1,
    "relationship_level1": "",
    "relationship_level2": "",
    "sentiment": "",
    "action_category": "",
    "action_type": "",
    "action_context": "",
    "action_status": ""
}
```
其中的id, start, end, text字段都是输入的.