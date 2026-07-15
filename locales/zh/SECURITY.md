> **Translation status (2026-07-15): historical pre-1.1 draft. The root English documents are authoritative; do not use this translation as the current operational or security contract.**

# 安全策略

## 漏洞呈报
请通过该仓库的 **GitHub Private Vulnerability Reporting**（安全 → 报告漏洞）提报安全漏洞。请勿为安全问题创建公开的 issue。

## 数据与隐私模型
本工具处理**您自己的 AI 交互日志**。请将生成的语料库和化身文件视为**私人的个人数据**：
- 语料库（`STUDIE/`）、已分类的切片（chunks）和填充的化身文件默认已列入 **.gitignore** —— 切勿提交真实的语料库。
- 提取器在**写入前**会脱敏 API 密钥、令牌（token）、电子邮件、类似 IP 的地址以及长数字串。
- **对健康、税务或其他敏感内容进行脱敏是操作人员的责任**，然后再将语料库或任何化身文件移出私密环境。
- 脚本本身不会将任何数据发送至任何地方；分类通过您所指定的智能体/LLM 运行——请单独审查该智能体的数据处理策略。

## 机密信息（Secrets）
任何曾经提交过的机密信息都必须进行**轮换（rotate）**，而不仅仅是从工作树（working tree）中移除。
