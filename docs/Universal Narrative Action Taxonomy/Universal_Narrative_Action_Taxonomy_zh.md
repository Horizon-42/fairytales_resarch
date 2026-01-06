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
| **`attack`** | **攻击** | Attempt to cause physical harm. | `ambush` (偷袭), `duel` (决斗), `spar` (切磋) |
| **`defend`** | **防御** | Block or mitigate harm. | `parry` (格挡), `shield` (护盾), `dodge` (闪避) |
| **`restrain`** | **束缚/控制** | Restrict physical freedom. | `bind` (捆绑), `imprison` (关押), `pin_down` (压制) |
| **`flee`** | **逃离** | Attempt to leave danger. | `panic` (惊慌), `strategic_retreat` (战略撤退) |
| **`travel`** | **移动/前往** | Significant change in location. | `quest` (征途), `sneak` (潜行), `chase` (追逐) |
| **`interact`** | **物品交互** | Manipulate physical objects. | `consume` (使用/消耗), `repair` (修理), `destroy_obj` (破坏物品) |

### II. Social & Communicative (社交与言语)
*Information exchange and relationship dynamics.*

| Code | Name (名称) | Definition (定义) | Context Tags (语境示例) |
| :--- | :--- | :--- | :--- |
| **`inform`** | **告知** | Convey information (neutral/true). | `report` (汇报), `reveal` (揭露), `explain` (解释) |
| **`persuade`** | **说服** | Attempt to influence logic/behavior. | `advise` (谏言), `beg` (恳求), `negotiate` (谈判) |
| **`deceive`** | **欺骗** | Convey false info to manipulate. | `lie` (撒谎), `feign` (佯装), `disguise` (伪装) |
| **`challenge`** | **挑战/挑衅** | Initiate conflict or competition. | `provoke` (激怒), `duel_proposal` (下战书), `threaten` (威胁) |
| **`command`** | **命令** | Force action via authority. | `order` (下令), `decree` (颁旨), `coerce` (胁迫) |
| **`betray`** | **背叛** | Break trust or allegiance. | `backstab` (背刺), `defect` (变节), `break_oath` (违誓) |
| **`reconcile`** | **和解/安抚** | Restore relationship or reduce tension. | `apologize` (道歉), `comfort` (安慰), `forgive` (原谅) |

### III. Transaction & Exchange (交易与交换)
*Transfer of resources, status, or value.*

| Code | Name (名称) | Definition (定义) | Context Tags (语境示例) |
| :--- | :--- | :--- | :--- |
| **`give`** | **赠予** | One-way resource transfer. | `gift` (礼物), `alms` (施舍), `legacy` (传承) |
| **`acquire`** | **获取** | Take or request resources. | `steal` (偷窃), `borrow` (借入), `seize` (抢夺) |
| **`exchange`** | **交换** | Two-way transfer. | `trade` (贸易), `bribe` (贿赂) |
| **`reward`** | **奖赏** | Positive feedback for service. | `promote` (升职), `pay` (支付), `honor` (册封) |
| **`punish`** | **惩罚** | Negative feedback for behavior. | `fine` (罚款), `exile` (流放), `execution` (处决) |

### IV. Mental & Cognitive (心理与认知)
*Internal state changes and decision making.*

| Code | Name (名称) | Definition (定义) | Context Tags (语境示例) |
| :--- | :--- | :--- | :--- |
| **`resolve`** | **下决心** | Firm commitment to a goal. | `decide` (决定), `vow` (发誓), `harden_heart` (铁石心肠) |
| **`plan`** | **谋划** | Formulate future strategy. | `scheme` (阴谋), `strategize` (布局) |
| **`realize`** | **顿悟/发现** | Shift from unknown to known. | `epiphany` (顿悟), `detect` (察觉), `deduce` (推理) |
| **`hesitate`** | **犹豫/动摇** | Loss of confidence or direction. | `doubt` (怀疑), `fear` (畏惧), `waver` (动摇) |

### V. Existential & Supernatural (生存与超自然)
*Changes in state of being or magical acts.*

| Code | Name (名称) | Definition (定义) | Context Tags (语境示例) |
| :--- | :--- | :--- | :--- |
| **`cast`** | **施法** | Release supernatural power. | `curse` (诅咒), `heal` (治疗), `summon` (召唤) |
| **`transform`** | **变形** | Change physical form. | `shapeshift` (变身), `grow` (生长) |
| **`die`** | **死亡** | End of life cycle. | `sacrifice` (牺牲), `perish` (殒命) |
| **`revive`** | **复苏** | Return to active state. | `awaken` (苏醒), `resurrect` (复活) |

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