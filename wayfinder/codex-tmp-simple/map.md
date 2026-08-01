---
id: CTM-MAP
title: Codex 临时工作区怎样做到低操作且容量有界
status: open
labels:
  - wayfinder:map
tracker: local-markdown
---

## Destination

形成一个可直接交给实现阶段的最小 Codex 临时工作区管理契约：平时无需手工维护，恢复能力有明确来源，磁盘占用有硬结果边界，并附带从现有 `codex-tmp` 平滑迁移的顺序与验收门槛。

## Notes

- 领域词汇以 [CONTEXT.md](CONTEXT.md) 为准。
- 本地图只负责决策、迁移顺序和验收合同；本轮 charting 不重写清理器、不批量删除目录。
- 用户已授权 agent 独立决策且当前 AFK。本地图不得创建依赖用户现场回答的 grilling 或 prototype 门槛；需要偏好判断时，以“最少操作、恢复优先、真实回收、现有存储复用”为排序原则。
- 使用现有 `/Users/qingpei/git/dotfiles` 仓库和 local-markdown tracker，不新建仓库，不把本机路径、session 信息或内部资产发布到公开 GitHub Issues。
- 研究优先核对 Codex 官方手册、当前本机实现、真实 inventory 与历史故障；不要从现有 3540 行实现反推需求。
- 官方 Codex managed worktree、chat history、snapshot restore 和 worktree retention 是产品能力；新方案优先复用，不平行复制。
- Git 仓库、构建缓存和工具链必须先路由到各自已有的规范工作区或共享缓存，临时工作区只保留不可替代检查点。
- 后续实现仍需使用 `python-dev`、`ops-safety` 和独立 verifier；任何真实删除必须另行经过迁移台账和恢复验证。

## Decisions so far

<!-- 关闭票据后仅追加一行结论索引；详细答案留在票据 resolution。 -->

- [当前管理流程为什么对 agent 和用户都太复杂](tickets/CTM-003.md) — 安全删除复杂度应下沉为深 Module；日常 Interface 应为零动作，异常只暴露限时保留与恢复。

## Not yet specified

- 容量目标最终应采用绝对 GiB、系统剩余百分比、按 owner 配额还是多信号组合，要等真实内容分层和恢复合同明确后再决定。
- 后台触发应由 hook、LaunchAgent、Codex automation 还是组合承担，要等最小状态机确定后再精确成票。
- 用户可见状态应进入 CLI、Codex task 更新还是系统通知，要等最小操作面和异常分类确定后再精确成票。
- 现有数百个 legacy unmanaged 目录的迁移批次和期限，要等分层规则可以自动判定后再展开。

## Out of scope

- 今晚不执行现有 `~/.codex/tmp` 的批量删除、强制 quarantine 或 purge。
- 不新建仓库、数据库、常驻网络服务或第二套 session 存储。
- 不替换 Codex 自带 chat history、managed worktree、snapshot restore 或 worktree retention。
- 不把所有项目编译环境长期保存在本机，也不把可再生产物包装成恢复证据。
