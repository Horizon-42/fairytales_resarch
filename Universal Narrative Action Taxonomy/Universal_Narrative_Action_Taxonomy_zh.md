# Universal Narrative Action Taxonomy (Bilingual)
# 通用叙事动作分类体系 (中英对照版)

**Purpose**: A micro-level annotation system for narrative actions, designed for LLM training.
**Structure**: **Action Type** (What) + **Context** (How/Why) + **Status** (Result).

---

## 1. Action Categories (动作分类详表)

### I. Physical & Conflict (物理对抗与交互)
*Direct bodily interaction, violence, or movement. / 直接的身体互动、暴力或移动。*

| Action Code | Name (名称) | Definition (定义) | Recommended Context Tags (推荐语境) |
| :--- | :--- | :--- | :--- |
| **`attack`** | **攻击** | Attempt to cause physical harm. <br>试图造成身体伤害。 | `ambush` (偷袭), `duel` (决斗), `mass_battle` (混战), `magical_blast` (法术轰击) |
| **`defend`** | **防御** | Block or mitigate harm. <br>阻挡攻击或减轻伤害。 | `parry` (格挡), `shield` (护盾/结界), `dodge` (闪避) |
| **`restrain`** | **束缚/囚禁** | Restrict physical freedom. <br>限制目标的物理自由。 | `bind` (捆绑), `imprison` (关押), `seal` (封印), `arrest` (逮捕) |
| **`flee`** | **逃离** | Attempt to leave a dangerous area. <br>试图脱离危险或控制。 | `panic` (惊慌逃窜), `strategic_retreat` (战略撤退), `obstacle_flight` (扔障碍逃亡) |
| **`steal`** | **窃取** | Take objects secretly. <br>未经允许秘密拿走物品。 | `pickpocket` (扒窃), `heist` (劫掠), `switch` (调包) |
| **`travel`** | **移动/前往** | Significant change in location. <br>显著的空间位置改变。 | `quest_journey` (征途), `flight` (飞行), `sneak` (潜行/闯入) |

### II. Communicative & Social (言语与社交)
*Information exchange and manipulation. / 信息交换与社交操纵。*

| Action Code | Name (名称) | Definition (定义) | Recommended Context Tags (推荐语境) |
| :--- | :--- | :--- | :--- |
| **`inform`** | **告知** | Convey true information. <br>传递真实信息（中性）。 | `report` (汇报), `rumor` (传闻), `confess` (招供/表白) |
| **`persuade`** | **说服/劝诫** | Attempt to change views or behavior. <br>试图改变对方观点或行为。 | `advise` (谏言), `beg` (恳求), `seduce` (诱惑), `debate` (辩论) |
| **`deceive`** | **欺骗** | Convey false information. <br>故意传递虚假信息。 | `disguise` (伪装/易容), `lie` (撒谎), `feign` (佯装/诈降) |
| **`command`** | **命令** | Force action via authority. <br>利用权力强迫对方行动。 | `decree` (圣旨/法令), `intimidation` (恐吓), `task_assignment` (派任务) |
| **`slander`** | **谗言/诬陷** | Make false accusations. <br>制造虚假指控以借刀杀人。 | `framing` (栽赃), `court_intrigue` (宫斗), `defamation` (毁谤) |
| **`promise`** | **承诺/发誓** | Establish a contract or credit. <br>建立契约或信用。 | `oath` (结义/发誓), `marriage_proposal` (求婚), `contract` (契约) |

### III. Transaction & Exchange (交易与交换)
*Transfer of resources or value. / 资源或价值的转移。*

| Action Code | Name (名称) | Definition (定义) | Recommended Context Tags (推荐语境) |
| :--- | :--- | :--- | :--- |
| **`give`** | **赠予** | One-way transfer (A to B). <br>资源单向转移。 | `alms` (施舍), `gift` (礼物), `inheritance` (遗产/传位) |
| **`request`** | **请求** | Express desire for resources. <br>表达获得资源的意愿。 | `demand` (索要), `pray` (祈祷), `borrow` (借) |
| **`exchange`** | **交换/交易** | Two-way transfer. <br>双向的资源转移。 | `barter` (以物易物), `buy` (购买), `bribe` (贿赂) |
| **`reward`** | **奖赏** | Positive feedback for behavior. <br>基于行为的正向反馈。 | `promotion` (升官), `title` (封爵), `treasure` (赏金) |
| **`punish`** | **惩罚** | Negative feedback for behavior. <br>基于行为的负向反馈。 | `execution` (处决), `exile` (流放), `fine` (罚没) |
| **`sacrifice`** | **献祭/牺牲** | Give up value for moral/magic result. <br>放弃高价值事物以换取结果。 | `self_sacrifice` (舍身), `offering` (祭品), `martyrdom` (殉道) |

### IV. Mental & Cognitive (认知与思维)
*Internal state changes. / 内在状态与认知的改变。*

| Action Code | Name (名称) | Definition (定义) | Recommended Context Tags (推荐语境) |
| :--- | :--- | :--- | :--- |
| **`observe`** | **观察** | Acquire sensory info. <br>获取视觉或感官信息。 | `spy` (窥视), `inspect` (视察), `watch` (守望) |
| **`realize`** | **识破/顿悟** | Unknown to Known. <br>从未知变为已知，看穿真相。 | `epiphany` (顿悟), `discovery` (发现), `see_through` (识破幻术) |
| **`investigate`** | **调查/寻找** | Actively seek info. <br>主动寻求信息的过程。 | `search` (搜查), `interrogate` (审问), `track` (追踪) |
| **`plot`** | **谋划** | Formulate plans internally. <br>在脑海中制定计划。 | `scheme` (阴谋), `strategy` (战略), `hesitate` (犹豫) |
| **`forget`** | **遗忘** | Loss of info or ignoring. <br>丢失信息或故意无视。 | `amnesia` (失忆), `ignore` (无视), `magic_forgetfulness` (孟婆汤) |

### V. Existential & Magical (生存与超自然)
*Changes in state of being. / 生命形态或魔法状态的改变。*

| Action Code | Name (名称) | Definition (定义) | Recommended Context Tags (推荐语境) |
| :--- | :--- | :--- | :--- |
| **`transform`** | **变形/化身** | Change physical form. <br>物理形态的根本改变。 | `shapeshift` (变身), `disguise_reveal` (显形), `growth` (变大/变小) |
| **`cast_spell`** | **施法** | Release supernatural power. <br>释放超自然力量。 | `curse` (诅咒), `bless` (祝福), `summon` (召唤), `heal` (治疗) |
| **`express_emotion`**| **情感表达**| Externalize strong emotion. <br>强烈的情感外化。 | `cry` (哭泣/哀悼), `laugh` (大笑), `rage` (狂怒) |
| **`die`** | **死亡** | End of life cycle. <br>生命周期的结束。 | `suicide` (自尽), `natural_death` (寿终), `murdered` (被杀) |
| **`revive`** | **复活** | Return from death. <br>从死亡状态恢复。 | `resurrection` (复活), `reincarnation` (转世), `awakening` (苏醒) |

---

## 2. Status Logic (执行状态逻辑)

Based on Claude Bremond's logic. Combine with Action Type.
基于布雷蒙叙事逻辑，用于标记动作的完成度。

| Status Code | Definition (定义) | Example (示例) |
| :--- | :--- | :--- |
| **`attempt`** | **尝试**<br>Action initiated, outcome pending. | Jing Ke throws the dagger. <br>荆轲投掷匕首。 |
| **`success`** | **成功**<br>Action achieved intended goal. | The dagger hits the target. <br>匕首击中目标。 |
| **`failure`** | **失败**<br>Action blocked or missed. | The dagger hits the pillar. <br>匕首击中柱子。 |
| **`interrupted`** | **打断**<br>Action stopped by external force. | "Hold the execution!" <br>刀下留人。 |

---

## 3. Data Structure Example (数据结构示例)

```json
{
  "narrative_event": {
    "agent": "Zhuge Liang",
    "target": "Sima Yi",
    "relationship": "enemy",
    "action_layer": {
      "category": "communicative",
      "type": "deceive",
      "context": "feign_confidence", 
      "status": "success"
    },
    "text": "Zhuge Liang plays the lute calmly, scaring Sima Yi away."
  }
}