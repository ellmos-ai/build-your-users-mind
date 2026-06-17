# 发布前 TODO：build-your-users-mind

**审计日期：** 2026-06-17
**审计员：** Claude（代表 Lukas Geiger）
**目标仓库：** `ellmos-ai/build-your-users-mind`（首先为私有）
**状态：** `development` —— Claude 路径已完成；存在私有参考实现。

---

## 准出拦截项（BLOCKERS）
> 必须在公开分发前解决。

- [x] **机密信息：** 跟踪的文件中无 API 密钥/令牌/密码。
- [x] **私人数据：** 无 PII/实际真实路径（泄漏扫描呈绿灯）。
- [x] **硬编码路径：** 所有脚本中均使用通用/相对路径。
- [x] **数据库文件：** 未跟踪 `.db` 文件。
- [x] **.env 文件：** 未跟踪 `.env` 文件。
- [x] **BACH 内部信息：** 无内部 BACH 文档。
- [x] **.gitignore：** 存在所需的最低配置项。
- [x] **许可证（LICENSE）：** 存在 MIT 许可证。
- [x] **README.md：** 英文版已完成。

## 高优先级（HIGH PRIORITY）
- [ ] 完善 Codex（rollout）+ Gemini（SQLite）的数据源适配器（目前为草稿）。
- [ ] 引入分类抽样检查/评分者一致性 Kappa 指标作为可选的质量控制步骤。
- [ ] 随附 `domains.json` 示例文件。

## 中优先级（MEDIUM PRIORITY）
- [x] 已添加 `SECURITY.md`。
- [ ] 自 v1.0.0 起建立 `CHANGELOG.md`。
- [ ] 撰写 `CONTRIBUTING.md`。
- [ ] Kimi 适配器（在首次使用时确认其日志格式）。

## 低优先级（LOW PRIORITY）
- [ ] 测试/冒烟测试套件、GitHub Actions CI、徽章。

## 有意不包含的内容
- 无私人语料库，无填充的化身文件（参见 `.gitignore`）。
- 无单个提示词级别的钩子（有意选择批处理 + 日志簿模式）。

---

## 状态（STATUS）

| 类别 | 状态 | 备注 |
|----------|--------|-------|
| 机密信息 | :green_circle: | 泄漏扫描通过（绿灯） |
| 私人数据 (PII) | :green_circle: | 无 PII/路径 |
| .gitignore | :green_circle: | 最低配置项 + 排除语料库/化身文件 |
| 语言（英语） | :green_circle: | README 为英文 |
| BACH 内部信息 | :green_circle: | 无 |
| 数据库文件 | :green_circle: | 无跟踪 |
| README.md | :green_circle: | 已完成 |
| 许可证 | :green_circle: | MIT |
| **整体状态** | **准备就绪** | 适用于私有发布；Codex/Gemini 适配器仍处于草案阶段 |

**审计日期：** 2026-06-17
**准出检查退出码：** `pending`（待定）

---

*基础模板：MODULES/_templates/TODO_TEMPLATE.md*
