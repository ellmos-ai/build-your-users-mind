> **Translation status (2026-07-15): historical pre-1.1 draft. The root English documents are authoritative; do not use this translation as the current operational or security contract.**

# TAXONOMY —— 8 种提示词类型 + 分类字段

> 独立版本（本模块自包含）。**方法论基础：** *Prompt-Archaeology* (L. Geiger) —— 对完整的人机交互协议进行分类的方法。

## 8 种提示词类型

| 类型 | 代码 | 定义 | 指标 |
|---|---|---|---|
| 初始提示 | **SP** | 启动新的分析或阶段 | 未引用先前的上下文 |
| 追问（主题） | **NT** | 深挖现有主题 | “那……怎么办？”等 |
| 追问（方法） | **NM** | 触发方法/工具/审查/搜索/智能体 | 动作动词 |
| 追问（控制） | **NS** | 管理顺序或优先级 | “等等”、“首先”、“停止”等 |
| 纠正 | **KO** | 纠正错误或假设 | 否定词、反例 |
| 确认 | **BE** | 验证中间状态 | 简短的同意/确认 |
| 方向转变 | **RA** | 根本性的方向转变 | 质疑整个框架前提 |
| 元提示 | **MP** | 关于过程或对话本身 | 过程术语 |

**边界情况：** SP 与 NT（新建 vs 关联）· NM 与 NS（触发方法 vs 仅重新排序）· BE 与 KO（“是的，但是……”通常是 KO）· RA 比 KO 更罕见，涉及整个框架前提。

## 分类字段（每个提示词）

| 字段 | 值 |
|---|---|
| `type_code` | SP/NT/NM/NS/KO/BE/RA/MP |
| `topic` | 简短主题（项目相关） |
| `is_decision` | 若为决策、偏好、规则、纠正或方向转变，则为 true |
| `decision_kind` | preference / correction / rule / direction_change / approval / rejection / process / none |
| `formulation_pattern` | 用户的特征措辞（原始措辞，简短） |
| `method_triggered` | WebSearch / WebFetch / Multi-Agent / Review / Cross-Model / Script / LaTeX / -- |
| `is_turning_point` | true/false |
| `outcome_signal` *(确定性的，阶段 0/1)* | praise / correction / reissue / none（派生自下一轮用户输入） |

## 偏差指标（阶段 4）
- **确认：纠正 (B:K) 比率** —— 不平衡暗示了赞同偏差；**无声的认可是不可见的**（未键入） → 纠正被过度代表。
- **每个主题的纠正率** —— 易错的主题。
- **主动：被动** —— 是由用户主导还是 AI 驱动？
- **方向转变率** —— 认知灵活性。
