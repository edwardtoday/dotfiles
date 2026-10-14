# AGENTS.d 参考资料

本目录保存不应常驻注入 agent 上下文的参考资料。完整专题流程优先放在全局 user skills；少量专题偏好可由全局 `AGENTS.md` 用明确触发条件和文件路径按需引用。项目约束放项目级 `AGENTS.md`。

- 全局基线规则：`~/.AGENTS.md`
- 参考资料目录：`~/.AGENTS.d/`（由 dotfiles 仓库中的 `AGENTS.d/` 软链生成）
- 本目录不是 Codex 的原生自动发现链；agent 只在有效指令显式引用或当前任务需要时读取，不自动加载整目录。

## 内容去向

- 跨项目、长期稳定的用户偏好：`~/.AGENTS.md`
- 有明确触发条件的专题流程：`~/.agents/skills/<name>/SKILL.md`
- 单个仓库的命令、架构边界和完成检查：项目级 `AGENTS.md`
- 可由工具强制的约束：CI、formatter、lint、hook 或配置
- 仅供人工查阅且不需要自动执行的资料：本目录

## 文件索引

- `codex-scheduled-tasks.md`：全局入口按需引用的 cron/Heartbeat 选择、运行及回读偏好
- `project-context.md`：何时需要项目级上下文文件，以及建议记录什么
- `dotfiles-context.md`：本仓库（dotfiles）特定上下文
- `documentation-policy.md`：文档同步策略与更新触发条件
- `tech-guides-index.md`：技术指南索引（本地优先，Raw 备用）
- `gitlab.md`：GitLab 约定、多行正文规范与私有 GitLab 访问

已迁移到 skills：

- `run-resumable-long-tasks`：长任务持久运行、检查点和恢复
- `optimize-end-to-end-systems`：设备、服务端与网络链路的端到端优化
- `use-y9000-pdf-ocr`：局域网 y9000 PDF / 图片 OCR
- GitLab CI 与静态扫描方法继续由现有 GitLab 专用 skills 承担

## 维护约定

- 只有高频、稳定、跨项目且无法由系统提示词可靠覆盖的偏好才进入 `~/.AGENTS.md`。
- 低频、专题化或步骤化流程优先做成 skill；少量按需引用的偏好必须在入口写明触发条件，不扩展为隐式全局规则。
- 仅对单个仓库有效的约定，优先写在该仓库根目录的项目级 `AGENTS.md`。
- 新增规则前先查重；能合并旧规则就不并列新增，避免同义重复。
- 定期删除已被系统提示词、skill、CI 或项目文档覆盖的重复内容。
