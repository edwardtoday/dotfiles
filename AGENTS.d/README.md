# AGENTS.d 扩展规范

本目录用于存放**非基线、低频、长篇或专题化**的规则，以避免 `AGENTS.md` 过重，并减少与不同工具/技能工作流的冲突。

- 全局基线规则：`~/.AGENTS.md`
- 扩展规则目录：`~/.AGENTS.d/`（由 dotfiles 仓库中的 `AGENTS.d/` 软链生成）
- 读取原则：仅在任务与该主题强相关时，才读取对应扩展文档

## 何时应迁出主文件

满足以下任一条件，优先迁到 `AGENTS.d/`：

- 规则需要长篇解释
- 只在某类任务中才会用到
- 属于专题方法论或经验沉淀
- 带有项目特例、工具特例或历史记忆

## 文件索引

- `project-context.md`：何时需要项目级上下文文件，以及建议记录什么
- `dotfiles-context.md`：本仓库（dotfiles）特定上下文
- `documentation-policy.md`：按项目规模分层的文档规范与更新触发条件
- `tech-guides-index.md`：技术指南索引（本地优先，Raw 备用）
- `long-running-runbook.md`：长任务心跳 / 恢复策略
- `gitlab.md`：GitLab 约定、多行正文规范与私有 GitLab 访问
- `workflow-protocols.md`：详细工作流、模式与阶段治理协议
- `global-memories.md`：跨会话高价值记忆与少量项目特例提醒
- `methodology-end-to-end-optimization.md`：端到端优化方法论
- `methodology-static-analysis-ci.md`：静态扫描 / CI / 自动化验证方法论

## 维护建议

- `~/.AGENTS.md` 只保留高频、稳定、跨项目的基线规则
- 项目特例优先放项目级 `AGENTS.md`
- 新增扩展文档时，顺手补齐这里的索引

## 维护约定（5 条）

- 高频、稳定、跨项目的规则，才进入 `~/.AGENTS.md`。
- 低频、专题化、需要长篇解释的规则，进入 `~/.AGENTS.d/*.md`。
- 仅对单个仓库有效的约定，优先写在该仓库根目录的项目级 `AGENTS.md`。
- 新增规则前先查重；能合并旧规则就不并列新增，避免同义重复。
- 新增、迁移、删除扩展文档后，顺手更新 `AGENTS.d/README.md` 索引；对失效、重复、长期不用的规则定期清理。

