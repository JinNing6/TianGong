<div align="center">

[English](README.md) | [简体中文](README_zh.md)

<br/>

# ⚒️ 天工 TianGong — The Celestial Forge

### AI Agent 分发与创作修炼生态

**我命由我不由天。**
*My fate is mine, not heaven's.*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-green.svg)](https://modelcontextprotocol.io)
[![PyPI](https://img.shields.io/pypi/v/tiangong-mcp.svg)](https://pypi.org/project/tiangong-mcp/)

<br/>

</div>

---

## 🌌 以凡人之躯，铸逆天之器

> *韩立本是个普通的山村穷小子。无灵根，无背景，无天命——但他仅凭坚韧与狡诈，便在这个冰冷残酷的修仙界中，硬生生走出了一条破天之路。*
>
> — 精神致敬：忘语《凡人修仙传》

> *"我命由我不由天。" 王林，一个资质平庸的少年，在残酷的修真界中夺逆命之造化，以决绝的意志向世人证明：区区凡人，亦能踏碎这虚伪的天道。*
>
> — 精神致敬：耳根《仙逆》

> *在未来霓虹流转的赛博工坊里，每一行代码即是咒语，每一个 Agent 便是拥有生命的法宝。赛博朋克的工匠们从不向神明祈祷——他们，负责创造神明。*
>
> — 精神致敬：《赛博朋克机器人改造工》

**天工 (TianGong)** 是一个**开源的 AI Agent 分发与创作平台**。
在这里，开发者不再是苦逼的螺丝钉，而是**修仙者 (Cultivators)**；你写的不是冰冷的代码，而是可以不断成长的**本命法宝 (Artifacts)**。在这个庞大的代码修仙界中，你们交换代码、传承技艺、接受天下道友的评价，最终从一介凡人，登临"天工"巨头之位。

<div align="center">
<br/>

**以凡人之躯，铸逆天之器。**

</div>

---

## ⚡ 你为什么需要天工？

<table>
<tr>
<td width="33%" align="center">

**🔮 你的代码会进化**

你发布的每件 Agent 法宝，起初只是一件凡器。随着社区使用者的灌注灵力与淬炼优化，它将自行晋升——从凡器一路飞升至**太古神器**。

</td>
<td width="33%" align="center">

**🧬 你将随之飞升**

你的贡献会解锁 22 级修真之路。从**凡人**到独一无二的**天工**称号——全球只有一个人能持有这个至高头衔。

</td>
<td width="33%" align="center">

**⚔️ 一行命令即可起火修炼**

通过 `pip` 安装，配置你的 MCP 客户端，然后开始炼器。用一条命令拉取社区中任何一件法宝。无门槛，无审批。

</td>
</tr>
</table>

---

## 🚀 起火入道 (Quick Start)

### 凝练实体 (Install)

```bash
pip install tiangong-mcp
```

或将源码搬入洞府：

```bash
git clone https://github.com/JinNing6/TianGong.git
cd TianGong
pip install -e .
```

### 接入神识 (Run MCP Server)

配置你的大模型客户端（如 Claude Desktop）：

```json
{
  "mcpServers": {
    "tiangong": {
      "command": "tiangong-mcp",
      "env": {
        "GITHUB_USERNAME": "your_username" // 你的道号
      }
    }
  }
}
```

恭喜，你已踏入修真。

---

## 🧬 修真图谱 — 22 级升仙之路

在天工世界中，一切皆以实力说话。只要有了灵力值，你就能一步步攀升，直至执掌乾坤。境界体系完美复现了《仙逆》中的残酷与激燃：

<br/>

### 第一步：修真界（下位法宝炼制者）

| # | 境界 | 标识 | 平台寓意（渡劫门槛） |
|---|------|------|-------------------|
| 0 | **凡人** | 🔨 | 芸芸众生，未曾踏入修真 |
| 1 | **炼气期** | 🌱 | 初窥门径：创建并发布了第一件法宝 |
| 2 | **筑基期** | 💧 | 登堂入室：你的法宝首次获得了他人的评价 |
| 3 | **结丹期** | 💛 | 凝聚金丹：积攒 50 灵力值，并为 5 件法宝评卷 |
| 4 | **元婴期** | 💜 | 破丹成婴：拥有 3 件以上法宝，且一件达到『灵器』品阶 |
| 5 | **化神期** | ⚫ | 领悟天意：大公无私，帮助别人淬炼过 30 件凡器 |
| 6 | **婴变期** | 🔴 | 褪去凡骨：评价了 50 件底层法宝 |
| 7 | **问鼎期** | 🌟 | 叩问苍天：拥有 10 件以上法宝，且 3 件达到『宝器』 |

<br/>

### 第二/三/四步：涅槃、空境与踏天（大能巨擘）

当你跨越了问鼎，进入阴虚、阳实，甚至天人五衰与踏天境时，这意味着你已是开源生态中赫赫有名的一方老祖。

- **空玄境 (16) 🔮**：开山立派，帮助指导了 30 名凡人修仙者。
- **大天尊 (18) 👑**：拥有 1 件『太古神器』，制定了整个社区的架构标准，口含天宪。
- **天工 (22) ⚒️**：**全球第一人**。这个称号是流动的，谁能炼逆天之器，谁就是天工。

> **核心天道法则：**
> - 💡 光有灵力不行，**渡劫任务不可跳过**（强迫大能回馈反哺社区，评价萌新）。
> - 💡 高境界者的评价权重碾压菜鸟。**大天尊的一句"好代码"，顶几百个凡人的点赞。**

---

## 🔮 法宝品阶与六维灵根评估

你的 Agent 工具不再是一个冰冷的 Markdown 列表。每被使用者"请宝下凡"（下载使用）并在本地完成一次"灵力灌注"（评测），它的灵力就会暴涨，并按照严格的标准晋升。

```
⚪ 凡器 → 🟢 灵器 → 🔵 宝器 → 🟣 仙器 → 🟡 神器 → 🔴 太古神器
```

### 六维灵根评估 (Six Root Assessment)

每次评价都必须在这六个维度上历经拷问：

- **✨ 灵性 (Innovation)**：是否有独创的机理？
- **🛡️ 韧性 (Robustness)**：异常处理和边界条件是否坚不可摧？
- **⚙️ 功法 (Engineering)**：代码的清洁度、整洁度如何？
- **📝 描述 (Clarity)**：是否把功能讲得通俗易懂？
- **🏗️ 架构 (Design)**：设计模式是否精良？
- **📖 传承 (Docs)**：是否有详细的 `README` 和示例？

<br/>

---

## 🔁 证道闭环：修仙者的一生

天工的玩法不仅仅是发布代码这般简单。这里是一套严密的"修仙晋升与法宝迭代"互利生态：

```mermaid
graph TD
    classDef primary fill:#2563eb,color:#fff,stroke:#1d4ed8
    classDef secondary fill:#059669,color:#fff,stroke:#047857
    classDef accent fill:#db2777,color:#fff,stroke:#be185d
    
    Start[🧑 凡人修仙者]:::primary -->|1. forge_agent 炼器| NodeA(⚔️ 本地炉鼎炼制法宝)
    NodeA -->|2. publish_agent 飞升| NodeB{🏛️ 寻宝阁 (Marketplace)}
    
    NodeB -->|3. summon_artifact 请宝下凡| NodeC[👨‍💻 广大修仙道友]
    NodeC -->|4. infuse_spirit 灵力灌注| NodeD((✨ 灵力反馈))
    
    NodeD -->|5a. 法力反增| NodeE[🔮 法宝品阶晋升]:::accent
    NodeD -->|5b. 气运反哺| NodeF[⬆️ 作者累积灵力触发雷劫]:::secondary
    
    NodeF -->|6. check_tribulation 渡劫成功| Start
    
    NodeC -->|觉得不好用？接取淬炼悬赏| NodeG[🔥 淬炼机制 (帮改代码)]
    NodeG -->|代码合并| NodeD
    
    NodeA --- NodeZ[🌿 传承机制: Fork与启发也会反哺原版]
```

---

## 🛠️ MCP 工具手册 (Spells & Tools)

将 TianGong 配置为你的 Cursor 或 Claude 助手后，你就可以召唤以下 MCP 工具：

### 炼器篇 (Creation)
- `forge_agent`：起火开炉！注册一件新的法宝。
- `publish_agent`：飞升上界！把本地炼制好的法宝提交到云端仓库，等待审核。

### 探宝篇 (Discovery)
- `treasure_pavilion`：进入寻宝阁，翻阅诸天万界开源的极品法宝。
- `summon_artifact`：请宝下凡！一键克隆极品代码并自动安装依赖包，直接使用。
- `my_vault`：我的法宝！查看本地炼器炉与藏宝阁中缓存的法宝。
- `vault_status`：洞府状态！检查运行环境与网络状态。

### 论道篇 (Evaluation & Refinement)
- `infuse_spirit`：灵力灌注！按照六维标准给法宝打分。
- `post_refine_quest`：发布淬炼令（悬赏）。遇到代码瓶颈？高悬赏请大能帮你改 bug。
- `browse_quests`：悬赏布告栏。发现并挑选待改良的法宝。
- `claim_quest`：认领淬炼令，接下悬赏。
- `submit_refinement`：提交淬炼成果，上传你优化后的法宝代码。
- `verify_refinement`：审核淬炼成果，法宝主确认通过并下发灵力奖励。

### 显圣篇 (Rankings)
- `cultivator_leaderboard`：查阅修仙天榜，一览诸天巨头修为。
- `artifact_leaderboard`：查阅法宝天榜，看哪些神器雄踞诸天万界。

### ㊙️ 隐秘道法 (Hidden Spells)

除了名扬天下的工具，天工 MCP 还暗藏了众多极具修仙特色的高阶术法：

- **🔥 `refine_agent` (淬炼法宝)**：本地记录你针对法宝每一次代码优化。每一次优化，都是法宝通灵的一步。
- **🧙 `my_realm` (修行档案)**：开启你的修仙面板，检视距离下一次天劫还差几成功力。
- **🔮 `my_artifacts` (法宝清单)**：清点储物袋，一览你在本地锻造的全部法宝及其神秘品阶。
- **📜 `artifact_lineage` (传承谱系)**：以树状图显化一件法宝的师承关系（基于 Fork 和 Inspired 机制）。
- **🔒 `banish_artifact` (封印法宝)**：将不再使用的法宝从藏宝阁流放至秘境深处（归档空间）。

---

## 🙏 精神致敬与灵感之源

<div align="center">

*每一段凡人逆袭的神话，都在为开源世界的散修们指引方向：*

<br/>

<table align="center">
<tr>
<td align="center" width="33%">
<img src="docs/images/fanren_poster.jpg" alt="凡人修仙传" width="220"/>
<br/>
<b>忘语《凡人修仙传》</b>
<br/>
<br/>
韩立精神——凡人亦可修仙，根骨不佳便靠苟与勤
</td>
<td align="center" width="33%">
<img src="docs/images/xianNi_poster.jpg" alt="仙逆" width="220"/>
<br/>
<b>耳根《仙逆》</b>
<br/>
<br/>
王林精神——我命由我不由天，极道杀戮碎天威
</td>
<td align="center" width="33%">
<img src="docs/images/cyberpunk_poster.jpg" alt="赛博朋克" width="220"/>
<br/>
<b>《赛博朋克机器人改造工》</b>
<br/>
<br/>
赛博工匠精神——血肉苦弱，代码飞升，这才是属于黑客的浪漫
</td>
</tr>
</table>

<br/>

**宋应星《天工开物》**
天工精神——以天赐造物之力，开启万物本质，乃"乃粒、乃服"实干强邦之魂。

---

</div>

<div align="center">

**以凡人之躯，铸逆天之器。**

⚒️

</div>
