> 英文版 (README.md) 为准；此翻译版可能会有滞后。

# build-your-users-mind

> **What you mind is what you get.**

**🌐 [EN](../../README.md) · [DE](../de/README.md) · [ES](../es/README.md) · [JA](../ja/README.md) · [RU](../ru/README.md) · [ZH](README.md)** — 英文版为准；翻译版可能会有滞后。

一份适用于任何 AI 智能体（Claude、Codex、Gemini/agy、Kimi 等）的配方，用于从自身的交互日志中构建一个经验性的、自完善的**关于其用户的心理理论模型（theory-of-mind model of its own user）**，并在用户不在时遵循用户的精神行事。

它通过**前馈（feedforward）**机制工作：智能体不是等待用户不在时无法到达的反响，而是*在反馈到来之前预测用户的反馈*，并将该预测用作引导/奖励信号——随后对照实际情况评估预测，以此不断优化。

## “我知道你想要什么。”

这句话道出了核心要义。智能体读取用户过去的提示词，提炼出**用户做出什么决定、他们如何表达以及他们是否满意**，并将其转化为一小组动态文档。在需要做出决策而用户无法取得联系时，智能体即可当即查阅这些文档。

它**不是**聊天机器人的角色扮演（persona），也**不是**繁重的框架——它是一个方法 + 少量脚本 + 文档模板。唯一与特定智能体相关的部分是*数据源适配器（source adapter）*（每个智能体在此读取自己的日志）。其余部分都是通用的。

## 工作原理 — feedback precognition

一个 0→4 的运行循环（参见 `templates/START.md`）：

| 步骤 | 文件 | 角色 |
|---|---|---|
| 0 | 项目 `DECISIONS.md` | 项目特定的决策优先（更为具体） |
| 1 | `WHAT-<USER>-SAID` | **基于证据的** 规则/决策（包含提示词 ID 引用） |
| 2 | `WHAT-WOULD-<USER>-SAY` | **precognition**（预知）——预测的反馈 + 置信度（🟢/🟡/🔴） |
| 3 | `WHAT-I-DID…` + `MY-ACTIONS.txt` | 根据预测所采取行动的日志 |
| 4 | `WHAT-<USER>-SAID-ABOUT…` | **评估**——预测 vs. 实际 → 优化 (1) 和 (2) |

质量指标 = **预期的反应与用户随后真实的反馈相吻合的频率。**
在 🔴（全新/无模式可循）时，规则是**向上呈报，不作无端猜测。**

### 流水线（构建模型）

1. **提取 (Extract)** (`scripts/corpus_extract.py`) —— 确定性地：仅从日志中提取人类键入的提示词，过滤合成的轮次，**脱敏敏感信息**，并将每个提示词链接到下一轮的 `outcome_signal`（赞扬/纠正/重新发出/无）。
2. **切片 (Chunk)** (`scripts/chunk_corpus.py`) —— 去重、可选领域、为群体（swarm）划分大小合适的切片。
3. **分类 (Classify)**（群）—— 8 类分类法（`TAXONOMY.md`）+ decision_kind + 措辞模式。分级群（领域负责人 × 切片执行者）；参见附带的 `skills/swarm-operations/`。
4. **聚合 (Aggregate)** (`scripts/aggregate_stats.py`) —— 类型分布、B:K 比例、转折点。
5. **撰写 (Author)** 从 `templates/` 生成化身文件，并将一个简短的指针**绑定 (Bind)** 到智能体自身的内存/规则文件中（Claude `CLAUDE.md`、Codex `GPT.md`/`AGENTS.md`、Gemini `GEMINI.md` 等）。

有关完整配方请参见 `SKILL.md`，每个智能体的日志位置请参见 `SOURCE-ADAPTERS.md`。

## Theory of us — 理论背景

该系统对**二元对（dyad）**（智能体 ↔ 用户）进行建模，而不仅是孤立地对用户进行建模——即“关于我们的理论（theory of us）”。
它基于以下理论支撑：
- 针对 LLM 智能体的**心理理论（Theory of Mind）**研究——预测对话者的心理状态并以此为条件能改善输出结果（例如，*ToM-SWE*, arXiv 2510.21903; *Infusing Theory of Mind into Socially Intelligent LLM Agents*, 2509.22887; *Persistent Memory & User Profiles*, 2510.07925）。
- **提示词考古学 (Prompt-Archaeology)** (L. Geiger) —— 分类完整的人机交互协议的方法，本模块复用了其 8 类型分类法（`TAXONOMY.md`）。
- 已知局限：LLM 的心理理论在**重复性案例中较为稳健，但在全新的或对抗性的变化下较为脆弱**——因此设立了置信度层级和“向上呈报，不作无端猜测”的规则。

## 偏差与局限（信任前必读）

- **无声的认可不可见** —— 用户键入的是纠正而非赞扬 → 模型会过度体现纠正，并向“挑剔”倾斜。请据此进行校准。
- **证据 ID 来自 LLM 综合提炼** —— 对承载核心逻辑的证据 ID 需对照原始语料库进行验证。
- **分类器偏差** —— 抽样抽查；严谨用途下请报告评分者间信度（inter-rater agreement）。

## 隐私与脱敏

提取器在**写入前**会对 API 密钥、令牌（token）、电子邮件、类似 IP 的地址以及长数字串进行脱敏。
**对健康、税务或其他敏感用户内容进行脱敏是智能体自身的责任**，然后再将语料库或任何化身文件移出私密空间。切勿提交真实的语料库——参见 `.gitignore`。

## Suggested GitHub topics

`theory-of-mind` · `llm` · `user-modeling` · `personalization` · `ai-agents` · `prompt-analysis` · `feedback` · `decision-support`

## 致谢与许可证

方法：Lukas Geiger 提出的 *Prompt-Archaeology*。模块与概念：Lukas Geiger (+ Claude)。
打包的依赖项：`swarm-operations` 技能。**MIT** —— 参见 `LICENSE`。
参考实现（私有，未出货）：基于作者自身日志构建的个人实例。
