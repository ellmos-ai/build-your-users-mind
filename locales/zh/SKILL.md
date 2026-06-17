---
name: build-your-users-mind
description: 适用于任何智能体模型（Claude、Codex、agy/Gemini, Kimi）的指南，用于从自身的交互日志中构建、维护其用户的经验性心理理论（ToM）模型，并绑定到内存/规则文件/系统提示词中。在“baue ein ToM/Entscheidungs-Avatar für meinen User”、“Theory of Mind System Nutzer-Modell”、“WHAT-WOULD-USER-SAY”、“feedback precognition”时激活。
---

# build-your-users-mind — 智能体通用 ToM 模块（反馈预知）

> **What you mind is what you get.** 一份**配方**，而非框架。每个智能体模型都以此构建*其*用户的 ToM 模型：评估自身数据 → 提炼决策模式 → 维护化身文件 → 绑定到自身内存/规则文件/系统提示词。
>
> **核心 = 反馈预知（feedback precognition / feedforward）：** 在用户反馈到来之前进行预测；在用户不在时将其作为控制信号；随后对照实际情况评估预测以实现自我改进。
>
> **模板：** `templates/`（化身文件）、`scripts/`（流水线）、`TAXONOMY.md`（8 种类型）、`skills/swarm-operations/`（分类群）。存在一个基于作者自身日志的**私有参考实现**，但未随附打包。
>
> **理论基础：** *Prompt-Archaeology*（方法，分类法见 `TAXONOMY.md`）+ ToM 研究（ToM-SWE arXiv 2510.21903；Persistent Memory & User Profiles 2510.07925）。

## 核心原则

LLM 从不直接查看原始的吉字节数据。**确定性脚本首先将数据精简**为人类键入的用户提示词的干净语料库；之后，**分类群（classification swarm）**才会进行语义化工作。
核心不在于“哪些提示词”，而在于**“做出了什么决策 → 产生了什么结果 → 用户是否满意”**。

## 6 个步骤

### 1. 明确数据源（数据源适配器）
找到您自己的交互日志。每个模型各不相同 → 参见 `SOURCE-ADAPTERS.md`。
**仅提取人类键入的真实提示词**（不包含工具执行结果、系统提示、钩子注入、上下文压缩摘要）。字段：`ts, project, session, text`。

### 2. 精简（确定性的，无 LLM 介入）
- 过滤合成的轮次，进行去重，聚合常规应答/微小确认。
- **随访关联：** 将每个提示词的下一轮（或几轮）用户输入派生为 `outcome_signal`（praise 赞扬 \| reissue 重新发出 \| correction 纠正 \| abandon 放弃 \| none）→ 作为满意度信号。
- 通过决策词典计算 **`decision_score`**（纠正/偏好/规则/控制）。
- **脱敏（持久化前的强制步骤）：** 脱敏密钥/令牌/密码/电子邮件——并根据用户情况，还需脱敏**健康/税务/IP 地址**。用户的敏感数据将被掩码。

### 3. 分类（群，分级 + stigmergy）
8 类分类法 **SP/NT/NM/NS/KO/BE/RA/MP**（定义见 `TAXONOMY.md`）+ `decision_kind`（preference/correction/rule/direction_change/approval/rejection/process/none）+ `formulation_pattern`（用户特征措辞）。对于大型语料库：领域负责人（Sonnet）指导切片执行者（Haiku）。

### 4. 生成化身文件
结构与 `templates/` 1:1 保持一致（复制模板，替换 `<USER>`/`<AGENT>`）：
`WHAT-<USER>-SAID.md`（已证实）· `WHAT-WOULD-<USER>-SAY.md`（预测 + 置信度）· `WHAT-I-DID-…md` + `MY-ACTIONS.txt`（行动日志）· `WHAT-<USER>-SAID-ABOUT-…md`（经验教训）· `PROMPT-LOG`（剪辑与线索）· `METHODIK.md`（含偏差警告）· `START.md`（0→4 循环）。

### 5. 绑定（至关重要！）
ToM 模型必须**切实投入使用**，而不仅仅是存在：
- 在智能体**自身的内存/规则文件/系统提示词**中写入简短的规则/指针（Claude: `CLAUDE.md`；Codex: `GPT.md`/`AGENTS.md`；agy: `GEMINI.md`；Kimi: `KIMI.md`）→ 指向 `START.md` 循环。**保持简短**（仅做指针，不放全文）。
- **优先规则：** 项目特定的 `DECISIONS.md` 优于横向的化身文件。
- **可选命令入口点（细节说明）：** 在三个深度层级加上一个编排器公开该循环 —— `read-my-mind`（预测，0→2，不执行动作）、`decide-like-me`（单次决策，0→2，作为工作流组件）、`be-my-avatar`（行动，完整 0→4，仅限可逆操作，记录日志）、`avatar-orchestrator`（跨多个决策的链式编排，将 🔴/不可逆项目打包成一个问题）。模板位于 `templates/commands/`。
- **版本化绑定：** 以项目副本中的循环/技能为规范版本；如果智能体还附带一个已注册的副本，则**版本号更高者优先**，旧的路由副本将被**替换** —— 项目主导，注册表跟随（避免版本漂移）。

### 6. 维护（自完善）
- **经验基础：** 定期重新运行脚本（日志无论如何都会持久化）—— **不要为每个提示词设置钩子**（避免幂等/多次注册陷阱；批处理更稳健）。
- **运行期（引导）：** 记录代表用户做出的假设 → 文件 (3)；收到反馈时 → 写入文件 (4) → 更新 (1) 中的规则，调整 (2) 中的置信度。

## 偏差与局限（必须一同提及）
- **无声的认可不可见** → 纠正被过度代表，使化身显得“苛刻”。
- **ToM 的脆弱性：** 在重复性情况下稳健，但在全新/对抗性变化下脆弱 → 设立置信度层级，在 🔴（全新/无模式）时**向上呈报，不作无端猜测**。
- 证据 ID 来自 LLM 综合提炼 → 针对关键决策，需对照原始语料库进行核对。

## 精简原则
唯一与特定模型相关的部分是**数据源适配器**（步骤 1）。配方、分类法、化身结构和绑定都是通用的。切勿过度设计。
