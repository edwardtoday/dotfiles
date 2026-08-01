---
id: CTM-MAP
title: Codex 临时工作区怎样做到低操作且容量有界
status: closed
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

- [Codex 官方恢复能力已经负责哪些状态](tickets/CTM-001.md) — 官方能力接管已持久化会话与 Git 恢复路径，tmp 只保留经验证无替代来源的非 Git 检查点。
- [当前 tmp 内容中真正不可替代的是什么](tickets/CTM-002.md) — 真正不可替代的仅是未锚定状态、小型检查点与活跃工作集，其余内容应路由或重建。
- [当前管理流程为什么对 agent 和用户都太复杂](tickets/CTM-003.md) — 安全删除复杂度应下沉为深 Module；日常 Interface 应为零动作，异常只暴露限时保留与恢复。
- [Git 仓库、构建输出和工具链应分别落在哪里](tickets/CTM-004.md) — Git、缓存、构建输出、工具链与证据各归唯一权威落点，tmp 只容纳极少数降级 clone 和唯一检查点。
- [最小生命周期和用户操作面应该是什么](tickets/CTM-005.md) — 采用事件驱动 reconcile；日常零操作，非活跃保留量有硬边界，活跃与阻塞字节必须完全归因。
- [现有 codex-tmp 如何无损迁移到最小实现](tickets/CTM-006.md) — 先资产路由，再双读、new-only、小批 legacy 和唯一 writer，旧状态只在恢复与回滚门槛通过后退役。
- [怎样证明新方案简单且不会再次失控](tickets/CTM-007.md) — 用零人工动作、真实回收时延、容量、恢复、并发、回滚和独立 verifier 的连续观察窗作为替换门禁。

## Not yet specified

无。容量合同、后台 Adapter、用户 Interface 和 legacy 迁移门槛均已在决策票据中明确。

## Out of scope

- 今晚不执行现有 `~/.codex/tmp` 的批量删除、强制 quarantine 或 purge。
- 不新建仓库、数据库、常驻网络服务或第二套 session 存储。
- 不替换 Codex 自带 chat history、managed worktree、snapshot restore 或 worktree retention。
- 不把所有项目编译环境长期保存在本机，也不把可再生产物包装成恢复证据。
