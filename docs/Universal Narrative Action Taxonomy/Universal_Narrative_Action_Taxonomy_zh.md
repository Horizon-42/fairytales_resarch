# Universal Narrative Action Taxonomy (Bilingual Extended)
# 通用叙事动作分类体系 (中英对照增强版)

**Version**: 2.0
**Purpose**: A high-fidelity annotation schema for narrative intelligence, emphasizing causality, character agency, and plot structure.
**Structure**: **Action** (What) + **Context** (How) + **Status** (Result) + **Function** (Role).

---

## 1. Action Categories (动作分类详表)

### I. Physical & Conflict (物理对抗与交互)
*Direct bodily interaction, violence, or movement.*

| Code | Name (名称) | Definition (定义) | Context Tags (语境示例) |
| :--- | :--- | :--- | :--- |
| **`attack`** | **攻击** | Attempt to cause physical harm. | `ambush` (偷袭), `duel` (决斗), `spar` (切磋), `brawl` (混战), `mass_battle` (大战), `magical_blast` (魔法冲击) |
| **`defend`** | **防御** | Block or mitigate harm. | `parry` (格挡), `shield` (护盾), `dodge` (闪避) |
| **`restrain`** | **束缚/控制** | Restrict physical freedom. | `bind` (捆绑), `imprison` (关押), `pin_down` (压制), `arrest` (逮捕), `seal` (封印) |
| **`flee`** | **逃离** | Attempt to leave danger. | `panic` (惊慌), `strategic_retreat` (战略撤退), `escape` (逃脱), `obstacle_flight` (设障逃离) |
| **`travel`** | **移动/前往** | Significant change in location. | `quest` (征途), `quest_journey` (踏上征程), `sneak` (潜行), `chase` (追逐), `wander` (漫游), `flight` (奔逃) |
| **`interact`** | **物品交互** | Manipulate physical objects. | `consume` (使用/消耗), `repair` (修理), `destroy_obj` (破坏物品), `craft` (制作) |
| **`steal`** | **偷窃** | (兼容) Take property/resources without consent. | `pickpocket` (扒窃), `heist` (盗取), `switch` (调包) |

### II. Social & Communicative (社交与言语)
*Information exchange and relationship dynamics.*

| Code | Name (名称) | Definition (定义) | Context Tags (语境示例) |
| :--- | :--- | :--- | :--- |
| **`inform`** | **告知** | Convey information (neutral/true). | `report` (汇报), `reveal` (揭露), `explain` (解释), `confess` (坦白), `rumor` (流言) |
| **`persuade`** | **说服** | Attempt to influence logic/behavior. | `advise` (谏言), `beg` (恳求), `negotiate` (谈判), `seduce` (引诱), `debate` (争辩) |
| **`deceive`** | **欺骗** | Convey false info to manipulate. | `lie` (撒谎), `feign` (佯装), `disguise` (伪装) |
| **`challenge`** | **挑战/挑衅** | Initiate conflict or competition. | `provoke` (激怒), `duel_proposal` (下战书), `threaten` (威胁) |
| **`command`** | **命令** | Force action via authority. | `order` (下令), `decree` (颁旨), `coerce` (胁迫), `assign_task` (分派任务), `intimidation` (恐吓), `task_assignment` (任务指派) |
| **`betray`** | **背叛** | Break trust or allegiance. | `backstab` (背刺), `defect` (变节), `break_oath` (违誓) |
| **`reconcile`** | **和解/安抚** | Restore relationship or reduce tension. | `apologize` (道歉), `comfort` (安慰), `forgive` (原谅) |
| **`slander`** | **诽谤/污蔑** | (兼容) Damage reputation via false accusations. | `framing` (栽赃), `court_intrigue` (宫廷阴谋), `defamation` (抹黑) |
| **`promise`** | **承诺/许诺** | (兼容) Commit to a future action/guarantee. | `oath` (誓言), `marriage_proposal` (求婚), `contract` (契约) |

### III. Transaction & Exchange (交易与交换)
*Transfer of resources, status, or value.*

| Code | Name (名称) | Definition (定义) | Context Tags (语境示例) |
| :--- | :--- | :--- | :--- |
| **`give`** | **赠予** | One-way resource transfer. | `gift` (礼物), `alms` (施舍), `legacy` (传承), `supply` (供给), `inheritance` (继承) |
| **`acquire`** | **获取** | Take or request resources. | `steal` (偷窃), `borrow` (借入), `seize` (抢夺), `loot` (掠夺) |
| **`exchange`** | **交换** | Two-way transfer. | `trade` (贸易), `barter` (以物易物), `bribe` (贿赂), `buy` (购买) |
| **`reward`** | **奖赏** | Positive feedback for service. | `promote` (升职), `pay` (支付), `honor` (册封), `bless` (赐福), `promotion` (晋升), `title` (封号), `treasure` (赏赐财宝) |
| **`punish`** | **惩罚** | Negative feedback for behavior. | `fine` (罚款), `exile` (流放), `execution` (处决), `demote` (贬职) |
| **`request`** | **请求/索取** | (兼容) Ask for resources, help, or permission. | `demand` (要求), `pray` (祈求), `borrow` (借用) |
| **`sacrifice`** | **牺牲/献祭** | (兼容) Give up something valuable (often self/offerings) for a goal or higher power. | `self_sacrifice` (自我牺牲), `offering` (供奉), `martyrdom` (殉道) |

### IV. Mental & Cognitive (心理与认知)
*Internal state changes and decision making.*

| Code | Name (名称) | Definition (定义) | Context Tags (语境示例) |
| :--- | :--- | :--- | :--- |
| **`resolve`** | **下决心** | Firm commitment to a goal. | `decide` (决定), `vow` (发誓), `steel_oneself` (强迫自己镇定), `harden_heart` (铁石心肠) |
| **`plan`** | **谋划** | Formulate future strategy. | `scheme` (阴谋), `strategize` (布局), `plot` (密谋), `strategy` (策略) |
| **`realize`** | **顿悟/发现** | Shift from unknown to known. | `epiphany` (顿悟), `detect` (察觉), `deduce` (推理), `discovery` (发现), `see_through` (看穿) |
| **`hesitate`** | **犹豫/动摇** | Loss of confidence or direction. | `doubt` (怀疑), `fear` (畏惧), `waver` (动摇), `confuse` (困惑) |
| **`observe`** | **观察/窥探** | (兼容) Watch closely to gather information. | `spy` (窥探), `inspect` (审视), `watch` (监视) |
| **`investigate`** | **调查/追查** | (兼容) Systematically search for facts/truth. | `search` (搜查), `interrogate` (审问), `track` (追踪) |
| **`plot`** | **阴谋/密谋** | (兼容) Scheme in secret (legacy code; overlaps with `plan`). | `scheme` (阴谋), `strategy` (策略), `hesitate` (犹豫) |
| **`forget`** | **遗忘** | (兼容) Lose or suppress memory/knowledge. | `amnesia` (失忆), `ignore` (忽略), `magic_forgetfulness` (魔法遗忘) |

### V. Existential & Supernatural (生存与超自然)
*Changes in state of being or magical acts.*

| Code | Name (名称) | Definition (定义) | Context Tags (语境示例) |
| :--- | :--- | :--- | :--- |
| **`cast`** | **施法** | Release supernatural power. | `curse` (诅咒), `heal` (治疗), `summon` (召唤), `enchant` (附魔), `bless` (赐福) |
| **`transform`** | **变形** | Change physical form. | `shapeshift` (变身), `grow` (生长), `shrink` (缩小), `disguise_reveal` (伪装揭露), `growth` (成长/变化) |
| **`die`** | **死亡** | End of life cycle. | `sacrifice` (牺牲), `perish` (殒命), `murdered` (被杀), `suicide` (自尽), `natural_death` (自然死亡) |
| **`revive`** | **复苏** | Return to active state. | `awaken` (苏醒), `resurrect` (复活), `regenerate` (再生), `resurrection` (复生), `reincarnation` (转世), `awakening` (觉醒) |
| **`cast_spell`** | **施法(旧)** | (兼容) Cast a spell (legacy code; overlaps with `cast`). | `curse` (诅咒), `bless` (赐福), `summon` (召唤), `heal` (治疗) |
| **`express_emotion`** | **表达情绪** | (兼容) Express strong emotion outwardly. | `cry` (哭泣), `mourn` (哀悼), `laugh` (大笑), `rage` (暴怒) |

---

## 2. Status & Logic (执行状态与逻辑)

*Standardized tags to describe the outcome of an action.*

| Tag | Meaning | Example |
| :--- | :--- | :--- |
| **`attempt`** | Action started, result unknown. | 挥剑斩去 (Result pending). |
| **`success`** | Goal achieved fully. | 击中要害. |
| **`failure`** | Goal missed completely. | 被对方躲过. |
| **`interrupted`**| Stopped by external force. | 剑被第三人拦下. |
| **`backfire`** | Result is opposite of intent (Harmful). | 用力过猛扭伤手腕. |
| **`partial`** | Partial success/failure. | 击中但未造成重伤. |

---

## 3. Narrative Function (叙事功能层)

*Meta-tags to describe the action's role in the story arc.*

* **`trigger`**: Inciting incident (引发后续情节的导火索).
* **`climax`**: Peak of conflict (冲突最高点).
* **`resolution`**: resolving conflict (结局/解决).
* **`character_arc`**: Defines personality change (人物弧光转变).
* **`setup`**: Preparation for future events (铺垫).
* **`exposition`**: Action serving primarily to reveal background info (交代背景/信息铺陈).