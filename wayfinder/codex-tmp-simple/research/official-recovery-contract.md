# Codex 官方恢复能力的责任边界

研究日期：2026-07-31

研究对象：Codex CLI `0.146.0`、当前 Codex 官方手册、OpenAI `openai/codex` 当前公开源码，以及本机只读状态观察。

## 结论

自建 `~/.codex/tmp` 不应继续扮演“每个会话的完整工作目录”。对启用了 history persistence 的非 ephemeral 聊天，Codex 已经分别负责保存 transcript、会话元数据和 Goal 状态；Scheduled 负责迁入其中的任务定义与运行记录；Codex-managed worktree 有自己的有限生命周期和删除前快照；Git 本身负责版本化源码与提交。

`~/.codex/tmp` 应收缩为**例外性的恢复检查点目录**：只保存尚未进入 Git、无法从远端或共享缓存重建、又确实需要跨轮次恢复的少量数据、脚本和外部操作游标。它不应保存仓库 clone、普通 worktree、构建依赖、构建输出，或与已启用的 Codex transcript、Goal、Scheduled 完全重复的状态副本，更不应保存“以防万一”的整套任务现场。

这个结论不是说 Codex 会备份所有文件。官方文档反而明确区分了聊天与当前工作树：聊天保留 transcript 和记录的工作目录，但恢复时从**当前**工作树重新读取文件。因此，“聊天可 resume”不能证明某个临时文件仍存在。[Projects and chats](https://learn.chatgpt.com/docs/projects)

## 证据等级

- **产品合同**：当前官方手册明确描述的用户可依赖行为。
- **公开实现**：OpenAI 当前公开源码中的实现细节；可以解释本机文件，但不是跨版本不变的产品承诺。
- **本机观察**：2026-07-31 对当前安装的只读检查；只证明当前机器此刻的状态。
- **未知边界**：官方手册和公开实现都没有明确承诺的内容；设计上不得把它当可靠备份。

## 能力矩阵

| 能力 | 官方负责保存什么 | 何时失效或不覆盖什么 | 能否替代自建 tmp |
| --- | --- | --- | --- |
| Chat history / resume | 对已保存、非 ephemeral 的 chat，保存 transcript、会话 ID/标题和记录的工作目录；`resume` 重新加载原 transcript | `--ephemeral` 不落 rollout，`history.persistence = "none"` 可关闭本地 transcript；不保存当前工作树的通用副本；显式 `delete` 会永久删除 transcript | 在确认 transcript 已持久化后，**替代其重复副本**；不能替代唯一文件检查点 |
| Codex-managed worktree | 为每个聊天提供隔离 Git checkout；同一聊天再次回到 Worktree 时复用其关联环境 | 默认只保留最近 15 个；归档聊天或超过配置上限会自动删除；依赖和缓存各占一份磁盘；永久 worktree 才不自动删除 | **替代 tmp 中的普通仓库 clone/worktree**；长期成果仍应 commit/branch/push |
| Managed-worktree snapshot restore | 删除 managed worktree 前保存快照；重开聊天时提供 restore | 只承诺 Codex-managed worktree；文档未公开快照格式、保留期、容量上限、加密/备份位置和逐类文件覆盖规则 | 可作 managed worktree 的产品恢复路径，**不可作通用备份或唯一归档** |
| Handoff | 在 Local、managed worktree 或匹配的远端项目之间移动聊天和 Git state；处理必要 Git 操作 | `.gitignore` 文件默认不随 Git handoff 移动；仅在本地 managed worktree 创建时，匹配 `.worktreeinclude` 的 ignored 文件可被复制；源 symlink 跳过 | **替代手工复制 Git 工作树到 tmp**；ignored/untracked 非 Git 数据仍需明确去向 |
| Goal mode | 持久化与聊天绑定的 objective、lifecycle status、token budget、tokens used 和 time used | 目标最多 4,000 字；它不保存逐阶段清单、执行游标、文件、进程或恢复审计；工作区仍须可用 | **替代完全重复的目标、Goal lifecycle 和预算字段**；不能替代任务检查点 |
| Scheduled tasks / automation | 保存任务 prompt、计划、启停状态和近期运行；chat 内任务可回到同一聊天上下文 | 本地任务要求机器开机、桌面 app 运行且项目仍在磁盘；web task 不保留本地目录/worktree；运行历史 retention 未公开 | 只替代**明确迁入 Scheduled 的触发计划**；不能替代外部调度器 ledger、ack/checkpoint 或持久执行引擎 |
| Shell snapshot | 当前公开 CLI 实现临时捕获 shell 环境，供 shell 执行一致性使用 | 正常对象释放时立即删除；3 天只是泄漏文件的 stale-cleanup 阈值；对象不是工作目录内容或 managed-worktree restore snapshot | **完全不能替代 tmp 文件恢复** |
| Appshots | 把前台窗口截图和可用文本作为聊天附件保存在本地 session file | 仅是附件；不是 worktree snapshot，也不保存被截图应用的真实数据文件 | 只替代“为了让模型看到界面”而另存的截图副本 |

## 分项证据与判定

### 1. Chat history 与 resume

产品合同：

- `/resume` 会重新加载选中聊天的 transcript，并保留原历史；CLI 的 `codex resume` 也可以按 ID 或最近会话继续。[CLI command reference](https://learn.chatgpt.com/docs/developer-commands?surface=cli#cli-codex-resume)
- `archive` 只把会话从活动列表移走，不删除 transcript；`unarchive` 可恢复。`delete` 才永久删除保存的会话。[CLI archive and delete](https://learn.chatgpt.com/docs/developer-commands?surface=cli#cli-codex-archive-and-codex-unarchive)
- `codex exec --ephemeral` 明确不把 session rollout 落盘；官方高级配置还允许以 `history.persistence = "none"` 关闭本地 transcript persistence。因此清理设计必须先确认目标 chat 确实可 resume，不能只因“Codex 通常保存历史”就推定它存在。[Non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode)；[History persistence](https://learn.chatgpt.com/docs/config-file/config-advanced#history-persistence)
- 官方项目文档明确说，聊天保存 transcript 和记录的 working directory，而 Codex 从当前 working tree 读取文件；持久项目说明应进入 `AGENTS.md` 或 checked-in documentation。[Projects and chats](https://learn.chatgpt.com/docs/projects)
- App Server 协议进一步明确：thread log 是持久 JSONL；archive 移动 rollout 文件，delete 删除 rollout 及其元数据和派生线程。[Codex app server](https://learn.chatgpt.com/docs/app-server)

本机观察：

- 当前 `$CODEX_HOME/sessions` 有约 2.2 千个 JSONL，约 11 GiB；`state_5.sqlite` 的 `threads` 表记录 `rollout_path`、`cwd`、标题、Git SHA/branch/origin、归档状态等元数据。数量会随正在运行的聊天变化。
- 当前 `$CODEX_HOME/worktrees` 为 0 B，但仍有大量可列出的历史 thread。这个组合直接验证了“聊天历史”和“工作目录”是两套生命周期。

判定：先确认聊天不是 ephemeral 且 history persistence 已启用，再从 `~/.codex/tmp` 排除 transcript、模型回复和工具输出的逐字副本。真正需要跨工具共享、脱离聊天独立保存的交接说明或验收证据仍应进入 Git 文档、票据或权威系统。

### 2. Codex-managed worktree 与 retention

产品合同：

- Worktree 是 Git checkout，共享 `.git` 元数据，但每个 worktree 拥有独立文件副本；managed worktree 默认在 `$CODEX_HOME/worktrees`。[Worktrees](https://learn.chatgpt.com/docs/environments/git-worktrees)
- managed worktree 面向单个聊天、轻量且可丢弃；长期环境应显式创建 permanent worktree。
- 默认只保留最近 15 个 managed worktree。Pinned chat、仍在进行的 chat 和 permanent worktree不会自动删除；归档关联聊天或超出配置上限时会自动删除。
- 删除前 Codex 保存 snapshot；聊天历史即便 worktree 已删除仍然存在，重开时可选择 restore。

未知边界：公开手册没有定义 snapshot 的内容清单、保留期、失败语义和可验证校验和。尤其不能据此断言 ignored 大目录、外部 symlink 目标、Git LFS 内容、socket、VM 磁盘或工作树外文件一定被保存。

判定：

- Git 仓库不应 clone 到 `~/.codex/tmp` 作为默认隔离手段。优先复用 canonical repo 和 Codex/Git worktree。
- 有价值的源码修改应形成 commit；需要协作或跨设备恢复时再 branch + push/MR。不要让 detached managed worktree snapshot 成为唯一副本。
- managed worktree 自带生命周期，因此自建清理器不应扫描、重命名或直接删除 `$CODEX_HOME/worktrees`；让 Codex/Git 管理它。

### 3. Handoff

产品合同：

- Local 与 Worktree 间 handoff 会移动聊天和代码，Codex 执行所需 Git 操作；同一聊天后来回到 Worktree 时会回到原关联 worktree。[Worktrees](https://learn.chatgpt.com/docs/environments/git-worktrees#working-between-local-and-worktree)
- 跨主机 handoff 会在目标主机创建或复用 worktree，并传输聊天和 Git state。[Remote connections](https://learn.chatgpt.com/docs/remote-connections#hand-off-a-chat-between-hosts)
- ignored 文件默认不会随 handoff 移动。对本地 managed worktree，可用仓库根目录的 `.worktreeinclude` 在创建时复制匹配的 ignored 文件；Codex 跳过源 symlink，且不覆盖目标已有文件。[Worktrees](https://learn.chatgpt.com/docs/environments/git-worktrees#copy-ignored-local-files-into-managed-worktrees)

判定：tracked source、staged/unstaged Git 变更和 branch 迁移不属于自建 tmp 的职责。确需跨 worktree 的少量 ignored 配置应放 `.worktreeinclude`；体积大的依赖、SDK、cache 不应通过它复制，而应使用共享缓存或 setup script 重建。

### 4. Snapshot restore、shell snapshot 与 Appshots 不是一回事

“snapshot”在本机至少指三种不同对象：

1. managed-worktree deletion snapshot：产品层文件恢复能力，范围只承诺 managed worktree。
2. shell snapshot：CLI 内部 shell 初始化快照。公开源码在 `ShellSnapshotFile` 正常释放时立即删除文件；3 天常量只用于清理缺少有效关联 session 或关联 rollout 已陈旧的泄漏文件。内容来自 shell，而非目录树。[`shell_snapshot.rs`](https://github.com/openai/codex/blob/2c005abb0765bfe3ef42a23fe88d5b806184fa83/codex-rs/core/src/shell_snapshot.rs)
3. Appshots：macOS 前台窗口截图和可用文本，作为附件存入 session file；CLI 可在 resume 后读取已有附件，但不能创建新的 Appshot。[Appshots](https://learn.chatgpt.com/docs/appshots)

判定：清理策略不得看到 `$CODEX_HOME/shell_snapshots` 就把它当工作区备份，也不得因存在聊天附件就推断原始文件已保存。

### 5. Goal mode

产品合同：

- `/goal` 把目标作为首个 prompt 和完成标准；可 pause、resume、edit、clear。每个 chat 保存自己的 context、messages、results 和 goal。[Long-running work](https://learn.chatgpt.com/docs/long-running-work)
- App Server 文档将其称为 persisted goal state，包含 objective、status、token budget、tokens used 和 time used；目标上限为 4,000 字。[Codex app server: Manage a thread goal](https://learn.chatgpt.com/docs/app-server#manage-a-thread-goal)
- 官方还要求“keep the workspace available while the goal is running”，并明确 Goal 不扩张 sandbox 或 approval 权限。

本机观察：`goals_1.sqlite` 存在独立 `thread_goals` 表，字段与官方协议一致；当前表内同时存在 active、paused、blocked 和 complete 状态。这验证 Goal 的 objective、lifecycle 和 accounting 是独立控制状态；它没有证明逐阶段清单、执行游标或恢复审计也被保存。

判定：只删除与 Goal 完全重复的 objective、Goal lifecycle、token/time budget 和 owner chat 绑定字段。逐阶段清单、外部命令或传输任务的业务游标、验收证据仍须由任务的权威载体保存。

### 6. Scheduled tasks / automation

产品合同：

- Scheduled 保存任务和近期运行；chat 内 task 使用原聊天上下文，standalone task 每次新建聊天。[Scheduled tasks](https://learn.chatgpt.com/docs/automations)
- 本地项目任务要求电脑开机、desktop app 运行且选定项目仍在磁盘。Web task 不会在运行间保留本地 folder 或 worktree。
- Git 项目可选择直接在 local project 或 dedicated background worktree 运行。频繁调度可能积累 worktree；官方建议归档不再需要的 runs，不要无意 pin。
- Scheduled 是调度器，不是长期守护进程：它适合定期重新进入聊天、轮询外部状态或触发 skill；它不承诺保留任意本地进程、文件描述符或 VM 状态。

判定：对于已经明确迁入 Scheduled 的任务，把触发计划和 Scheduled 自己的运行状态交给产品；外部调度器仍在使用的 durable ledger、ack/checkpoint 不能据此删除。长进程本身交给合适的进程管理器，tmp 只保存无法从服务端或进程管理器重建的 checkpoint。

## 应明确从自建 tmp 职责中删除的内容

以下内容应成为硬性排除项，而不是“可以早点清理”的弱建议：

1. **已确认持久化的聊天与控制面副本**：非 ephemeral chat 的 transcript 逐字副本、与 Goal objective/lifecycle/budget 完全相同的字段、与已迁入 Scheduled 的 trigger 定义完全相同的字段。逐阶段恢复清单、外部调度 ack/checkpoint 和独立验收证据不在此排除项内。
2. **Git 仓库副本**：可从 canonical repo、remote 或 Git object database 重建的完整 clone；为隔离而建的普通 worktree；仅用于阅读的仓库镜像。
3. **Git 可表达的独有修改**：有价值的 dirty 修改应 commit 到明确 recovery/feature branch；需要远端容灾时 push。tmp 不能成为未提交代码的长期归档层。
4. **可再生依赖与输出**：`node_modules`、Rust `target`、Python virtualenv、Gradle/Maven/Cargo/npm cache、`dist`、coverage、编译工具链解包目录、容器层和测试数据库副本。
5. **官方托管目录**：`$CODEX_HOME/sessions`、`archived_sessions`、`worktrees`、`shell_snapshots`、attachments 和产品 SQLite。自建 cleaner 不拥有这些目录，也不应把它们纳入自己的 retention 状态机。
6. **已有权威来源的证据副本**：可按 ID 从 GitLab/GitHub、对象存储、CI job、MR、issue、Lark 或其他系统重新取得的完整响应。只保留稳定 ID、URL、必要 hash 和简短结论。

## tmp 仍应负责什么

仅保留同时满足以下全部条件的对象：

1. 当前还未交付到 Git、对象存储或其他权威系统；
2. 无法从输入、远端 ID 或共享缓存合理重建；
3. 丢失会实质阻断跨轮次恢复，而不只是多跑一次命令；
4. 有明确 owner、用途、最小恢复说明和退出路径；
5. 尺寸受控，不包含可剥离的依赖、clone、cache 或 build output。

典型允许项：尚未上传的唯一采集数据、不可重放外部操作的最小 checkpoint、需要人工验收的唯一中间制品、恢复长传输所需的清单与校验和、短小的一次性脚本。即便允许，也应尽快迁到任务的现成仓库、对象存储或权威业务系统。

## 对后续设计的直接约束

- `codex-tmp create` 不应成为每个任务的强制前置动作；只有任务确认产生“允许项”时才创建。
- 创建时不做容量预留或拒绝准入；磁盘压力应触发报告和对可再生内容的清理，而不是阻止新任务开始。
- 不以 session 是否 active 决定整个目录能否清理。active chat 只保护真正的唯一 checkpoint，不保护 clone、依赖和构建输出。
- 不再为每个目录复制 Goal 已持久化的 objective/lifecycle/budget。owner heartbeat、审计与 quarantine 只在它们确实保护唯一 checkpoint 时保留；删除可再生内容不应因聊天恢复窗口等待数天。
- Git 工作应直接进入现成 canonical repo 或它的 worktree。GitHub 项目使用现有 `/Users/qingpei/git/github`；Sansi 项目优先 `/Volumes/T7/git-sansi`。
- 一项任务在 Git 或经过 hash/ID 校验的远端权威系统中已有产物后，tmp 中相同内容立即失去保留理由。聊天附件只属于本地 session，不单独构成权威备份。

## 仍然未知、不得过度承诺的边界

- managed-worktree restore snapshot 的精确文件集合、大小限制、保留期和校验机制未公开。
- session JSONL、attachments 和产品数据库的长期版本兼容、云端备份与灾难恢复 SLA 未见公开承诺。
- Handoff 对特殊文件、Git LFS、submodule、超大 ignored 文件和中断恢复的完整语义未被当前文档穷尽。
- Scheduled task 的产品 retention 时长和历史 run 上限未在当前手册中给出。

因此最终方案应依赖公开的职责边界，而不是依赖这些未知实现细节：已持久化、非 ephemeral 的聊天由 Codex 保存，源码由 Git 保存，明确迁入 Scheduled 的触发计划由 Scheduled 保存，唯一非 Git 检查点才由精简后的 tmp 暂存。
