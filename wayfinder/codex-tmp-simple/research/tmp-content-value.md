# `~/.codex/tmp` 内容价值分层

快照时间：2026-07-31 23:56-2026-08-01 00:03（Asia/Shanghai）

## 结论

`~/.codex/tmp` 中真正不可替代的不是“任务目录”，而只有三类状态：

1. 尚未进入规范工作区或远端的 Git 状态，例如 dirty index、无 upstream 的本地提交、尚未整合的 linked worktree；
2. 无法从会话记录、规范工作区、远端 Git 或共享缓存重建的小型任务检查点和原始证据；
3. 进程仍持有期间的工作集，直到进程退出并验证替代来源可用。

其余内容应被视为有来源的副本或可再生产物，而不是恢复证据。`active`、`keep`、`complete` 只是生命周期信号，不能证明目录内每一个字节都有恢复价值。领域定义也明确把规范工作区、任务检查点、可再生产物、恢复引用和物理回收分开，[`CONTEXT.md`](/Users/qingpei/git/dotfiles/wayfinder/codex-tmp-simple/CONTEXT.md) 中的对应定义是本报告的分类基准。

当前直接 `du -x -sk` 快照为 **61.13 GiB**；15 分钟容量缓存为 `65,510,322,176 bytes`，即 **61.01 GiB**。两者的约 0.12 GiB 差异来自活跃目录在测量间继续变化，不影响 tmp 已越过 60 GiB hard watermark 的判断。缓存同时显示本机仍有约 95 GiB 空闲。来源：[`capacity.json` 第 2-10 行](/Users/qingpei/.local/state/codex-tmp/capacity.json#L2-L10)和[`tmp-lifecycle.json` 第 14-24 行](/Users/qingpei/.codex/tmp-lifecycle.json#L14-L24)。本轮 `codex-tmp inventory` 报告 27 个 active、61 个 complete、15 个 keep、218 个 unmanaged；根目录实测有 321 个目录和 272 个散落文件。按状态计，active 约 26.68 GiB、complete 15.21 GiB、keep 6.47 GiB、unmanaged 12.71 GiB。治理对象已经明显不是少数“任务目录”，而是混合了工作区、副本、缓存、证据和遗留散件的存储池。

## 当前最大样本

以下为 `du -sk ~/.codex/tmp/* | sort -nr` 的实时 allocated-size 快照；前 6 项合计 **30.73 GiB，占整个 tmp 的 50.4%**。

| 目录 | 当前大小 | 内容判定 | 不可替代部分 | 主要替代来源 |
| --- | ---: | --- | --- | --- |
| `quectel-gcc-921-ci` | 9.85 GiB | 3 个 tracked-clean 的 GitLab 完整仓库副本（9.26 GiB）+ 解压工具链及压缩包（0.59 GiB） | 尚未确认的任务结论或日志，而不是 3 个 clone | `/Volumes/T7/git-sansi` 已有同源路径、GitLab、可校验工具链制品 |
| `mr-pipeline-fixes-20260729` | 7.41 GiB | 2 个 tracked-clean 的 GitLab 仓库；其中 `.git` 对象库约 3.15 GiB，源码/SDK 树约 4.26 GiB | 若分支未推送，则是 HEAD/ref；不是完整对象库和第二份工作树 | T7 已有同源路径 + 受保护分支/worktree |
| `embedded-ci-1943-probe` | 4.94 GiB | 单个完整 clone；`.git` 1.19 GiB，`msp/out` 1.14 GiB，另有 0.33 GiB `node_modules.tar` | 13 个 tracked dirty path 及其验证上下文 | dirty patch/commit + T7 canonical repo；构建输出和依赖包可重建 |
| `sonar-scope-audit-20260730` | 3.79 GiB | 3 个 tracked-clean GitLab clone 占几乎全部空间；ledger/evidence 不到 0.2 MiB | `workitems.tsv`、mapping、measure/evidence 小文件 | T7 已有同源路径；小型台账才是 checkpoint |
| `health-eye-pricing-research-20260731` | 2.50 GiB | 5 个 `/Users/qingpei/git/deep-research` linked worktree；998 个文件五份逐字节相同，额外重复约 1.99 GiB | 5 个无 upstream 的 research 分支及最终整合结果 | 主仓 Git 对象库 + 分支；整合后应受管移除 worktree |
| `gitlab-ci-matrix` | 2.25 GiB | 24 个 Git 工作区及少量 artifacts/ledger | 历史审计认定的 standalone patch、ledger、snapshot、CI ZIP 证据 | T7/GitLab 提供 clean 源码；证据单独封装 |

这组样本说明容量不是由“恢复状态”主导，而是由**完整 Git 工作树、重复 `.git` 对象库、SDK/vendor 树和构建环境**主导。2026-07-28 的首批台账也出现同样结构：71.75 GiB 的前 10 项中，多项单独包含 5.87-16.08 GiB 可再生或可重克隆 bulk，而真正的 blocker 是少量 dirty/local-only Git 状态与 ledger，[`batch-01-results.tsv` 第 2-11 行](/Users/qingpei/.codex/tmp/codex-tmp-inventory-20260728/batch-01-results.tsv#L2-L11)。

## 七层价值模型

| 层 | 真实恢复价值 | 可验证替代来源 | 当前/历史规模证据 | 误删后果 | 应采取的合同 |
| --- | --- | --- | --- | --- | --- |
| 规范工作区副本 | 副本本身低；只有未锚定的 ref/index/dirty diff 高 | 同源 T7 repo、远端 commit、主仓 worktree metadata | 当前前 6 大目录中至少 28 GiB 是 Git 工作区或其源码树；历史上 45 个工作目录中 42 个 clone 和 2 个 worktree 可迁走 | clean 且 HEAD 可达时只是重取成本；local-only ref/dirty index 被删则永久丢工作 | 先验证 HEAD/tree/ref/dirty state，再把唯一状态落到规范仓库；tmp 不保留完整 clone |
| 可再生产物 | 通常为零 | lockfile、源码、构建命令、制品源、共享 package/build cache | 当前常见名称下至少有 `target` 4.11 GiB、`node_modules` 1.14 GiB、`build` 1.00 GiB、`dist` 0.12 GiB；历史 batch 2/3 又实际回收约 7.90 GiB | 需要重建、下载或重新测试；不会丢设计决策 | 验收取证后立即删；symlink-only runtime link farm 例外，因为删除不回收 package bytes 却破坏工具解析 |
| 任务检查点 | 高，但应很小 | 无；它本身就是最小恢复源 | 当前 `sonar-scope-audit` 的 ledger/evidence <0.2 MiB，而其 repo 副本 3.79 GiB；说明 checkpoint 与工作区体积相差四个数量级 | 任务可从会话读到“做过什么”，却无法继续精确批次、游标、选择或未提交工作 | 只保留 ledger、patch/bundle、命令/版本、外部引用和下一步；默认目标远低于 512 MiB |
| 证据归档 | 中到高，取决于能否从系统 of record 重新查询 | GitLab job/artifact/API、报告仓库、对象存储 | 独立 evidence store 当前约 230 MiB；一次迁移控制目录却保留 0.632 GiB | 审计可重复性下降；但重复保存公开/远端可取 trace 只增加成本 | 保存不可重取、用于结论的最小原始证据 + SHA-256 + 来源 URI/ID；其余保留引用 |
| 共享缓存 | 恢复价值为零，性能价值可测 | package registry、compiler/toolchain artifact、CAS/build cache | 现有 tmp 没有清晰共享缓存边界；历史 `node-mrs-group1` 单项含 7.51 GiB SDK/cache/build bulk | cache miss 和重下载，不应导致任务状态丢失 | 移出 tmp，按 cache key、总额和 LRU 独立治理；任务只记录 key，不复制缓存 |
| 活跃进程依赖 | 暂时高；进程退出后迅速降为副本/缓存 | 进程状态 + 已验证 canonical copy | 历史 `cicd-rollout` 仅因 VM open FD 保留约 0.23 GiB 工具链和 1 个 Git 目录；其余 18.721 GiB 已回收 | 活跃编译/VM 可能立即失败，甚至写入半截 | FD/cwd 只作为短租约 blocker；进程结束后重新分类，不自动转成长期 `keep` |
| 未知遗留物 | 未知，不等于高价值 | 内容签名、Git/owner/session/mtime/remote 检查 | 当前 218 个 unmanaged，另有 272 个根级散件；数量噪声远高于已受管任务 | 直接删可能命中唯一 patch、密钥风险证据或仍被引用的文件 | 先轻量识别；无法分类则有期限地隔离或要求生成最小 checkpoint，不能无限期按“可能有用”保留 |

### 1. 规范工作区副本

`cicd-rollout` 是最有说服力的实证：45 个 Git 工作目录经过 HEAD/tree、dirty 状态、refs、symlink 和进程检查后，42 个完整 clone 删除、2 个 linked worktree 受管移除，只剩 1 个进程持有目录；任务从约 19 GiB 降至 0.287 GiB，回收 18.721 GiB，[`closeout.md` 第 7-15 行](/Users/qingpei/.codex/tmp/cicd-rollout-migration/closeout.md#L7-L15)。另一个 10.85 GiB SDK clone 也在 exact HEAD/tree 可从 T7 恢复后删除，[`final-validation.md` 第 14-21 行](/Users/qingpei/.codex/tmp/cicd-rollout-migration/final-validation.md#L14-L21)。

因此，Git 目录的价值必须按状态拆开：

- clean + exact commit/tree 在 T7 或远端可达：副本，可回收；
- clean + local-only commit/ref：提交对象不可替代，工作树通常可替代；
- dirty tracked/index/untracked：差异不可替代，应 commit/push、bundle 或 patch/checksum 后再回收；
- linked worktree：唯一状态进入主仓后，用 `git worktree remove/prune`，不能直接 `rm`。

### 2. 可再生产物和共享缓存

历史 batch 2/3 的 cleanup ledgers记录了约 3.22 GiB 和 4.67 GiB 的可再生产物清理，主要是 `target`、`node_modules` 和可重新安装 runtime。当前实现也明确把 Cargo `target` 和本地安装型 `node_modules` 排除在恢复指纹之外，并保留只含 shared-runtime symlink 的 link farm，[`TOOLS.md` 第 62-66 行](/Users/qingpei/git/dotfiles/bin/TOOLS.md#L62-L66)。这条边界正确：恢复内容和性能内容必须分开。

但“可以重建”并不等于“应在每个任务重建”。大工具链、SDK、npm/Cargo/uv 缓存应进入现有 T7 asset/cache 或用户级共享缓存，由独立总额和淘汰策略控制；tmp 只保存版本、校验和、来源和 cache key。

### 3. 检查点与证据

一次成功迁移把 24.276 GiB 的两个任务主体收缩后，新增控制/恢复证据仅 0.632 GiB，净回收仍为 23.644 GiB，[`closeout.md` 第 17-25 行](/Users/qingpei/.codex/tmp/cicd-rollout-migration/closeout.md#L17-L25)。但 0.632 GiB 仍偏大，因为它包含迁移脚本、重复 evidence、bundle 和 bytecode；长期合同应进一步只留：

- `workitems.tsv` / progress / decision ledger；
- unique dirty patch、Git bundle 或 protected ref；
- 不可重新拉取的原始证据及 SHA-256；
- canonical workspace、remote commit、artifact/job ID；
- 恢复命令和未完成风险。

当前独立 evidence store 约 230 MiB，checkpoint object store 只有 4 KiB；这说明可以把“恢复所需的小对象”从 61 GiB 工作区中分离，而不需要把整个 task 目录留作恢复凭据。

### 4. 活跃进程依赖

进程引用是删除门，不是保留理由。历史迁移中 VM 持有两个 tmp 路径和工具链 FD，因此未终止 VM，也未删相应目录，[`final-validation.md` 第 23-27 行](/Users/qingpei/.codex/tmp/cicd-rollout-migration/final-validation.md#L23-L27)。正确语义是“稍后重评”：FD 消失且 T7 checksum copy 可用后应立即回收，不应把任务永久标记为 `keep`。

### 5. 未知遗留物和事故教训

早期清理器审查曾发现四类会把“看似可删”变成真实数据损失的事故窗口：restore 与 purge 竞态、完成任务被并发 heartbeat 重新激活、深层 dirty Git 漏检、clean repo 的 local-only history 漏检，[`review.md` 第 3-16 行](/Users/qingpei/.codex/tmp/codex-tmp-auto-adopt-review-20260728/review.md#L3-L16)；后续复核还明确指出过“clean 但无 remote/upstream 的提交可被永久删除”和 heartbeat 到达时 active path 暂时消失的问题，[`final-review-after-race-and-framing-fixes.md` 第 1-13 行](/Users/qingpei/.codex/tmp/codex-tmp-auto-adopt-review-20260728/final-review-after-race-and-framing-fixes.md#L1-L13)。这些是历史发现，不代表当前实现仍含同一缺陷；它们证明删除门必须验证**可恢复来源**，不能只看 status、mtime 或目录名。

另一个近期事故是把 symlink-only `node_modules` 当成本地依赖删除：实际回收 0 bytes，却造成 Artifact Tool 模块解析失败。当前合同已把这类 link farm 明确列为保留例外，[`TOOLS.md` 第 64 行](/Users/qingpei/git/dotfiles/bin/TOOLS.md#L64)。这再次说明应按“真实 allocated bytes + replacement consequence”判断，而不是按名字匹配。

元数据本身也不能作为价值证明：当前 18 个 active manifest 没有 owner session、没有 required path，却占约 **25.06 GiB**；23 个同类 complete manifest 占 4.55 GiB，4 个 ownerless keep 占 3.22 GiB。最大的 ownerless active 正是 `quectel-gcc-921-ci`、`mr-pipeline-fixes-20260729` 和 `embedded-ci-1943-probe`。泛化的 “Task files may be required” 不能替代具体的恢复引用；否则 `active/keep` 会成为整个目录无限保留的同义词。

## 对后续最小管理契约的约束

1. **恢复单位必须从目录改为引用和小检查点。** 每个任务最多需要：canonical refs + optional checkpoint bundle + short lease；不需要持久化整个工作区。
2. **状态不能保护所有字节。** active/keep 只保护不可替代部分和正在使用的工作集；可再生产物仍可在验收后回收。
3. **Git 路由优先于清理。** `git.sansi.net` 先查 T7；local-only 状态迁入 branch/worktree，再释放 tmp clone。GitHub/本地仓库同理使用已有 canonical repo。
4. **缓存必须独立。** 共享 cache/SDK/toolchain 有自己的路径、key、quota 和 LRU；tmp 中出现大 cache 是路由失败，不是需要更长 retention。
5. **完成应触发收缩而非等待。** 完成时先删可再生输出、归位 Git 状态、提取 checkpoint；72 小时/7 天/14 天只适用于已经很小的恢复 stub，而不是数 GiB body。当前文档规定普通完成任务仍等待 72 小时、owner 7 天和 quarantine 14 天，[`TOOLS.md` 第 64 行](/Users/qingpei/git/dotfiles/bin/TOOLS.md#L64)，这应从“主体保留期”降级为“最小 checkpoint/stub 保留期”。
6. **未知有短期保护，但没有无限期豁免。** 先识别 Git、process、checkpoint 和 secrets 风险；到期仍无法分类时，留下 inventory/checksum 和恢复说明后隔离，而不是自动 `keep`。

现有成功样本证明这不是理论目标：`annual-log-ci-20260719` 已从约 6.486 GiB 主体压缩成 8 KiB recovery stub，同时保留 T7 commit 和 evidence SHA-256，实际回收 6,964,531,200 bytes；该结果与 98/98 测试记录在[`tmp-size-control closeout` 第 12-25 行](/Users/qingpei/.codex/tmp/tmp-size-control-implementation-20260729/closeout.md#L12-L25)。当前却没有 pending compaction，说明问题不在“压缩模型做不到”，而在它仍是显式、低采用率的旁路。

## 证据边界

- 本轮只读执行了 `codex-tmp inventory`、`du -sk`、`find`、`git status --porcelain -uno`、`git rev-parse`、`git config --get remote.origin.url`（输出前去除 userinfo）和有限的进程检查；没有 fetch、checkout、move、quarantine、purge 或删除。
- 规模是 APFS allocated size 的点时快照，任务继续运行会变化。分类覆盖全局状态计数、当前前 30 大项和前 8 大项的定向拆分，不是 593 个根级条目的逐文件审计。
- Git dirty 计数只覆盖 tracked status；报告没有宣称所有 untracked、refs、reflogs 或远端 reachability 已完成逐仓验证。任何实际删除仍须逐项验证。
- 历史事故引用的是当时的审查证据；当前实现的修复状态不在本票据范围内。
- 未读取或输出 secret 值；remote URL 在采样输出前去除 userinfo，报告只保留替代来源类别。

## 来源

- 当前容量：[`~/.local/state/codex-tmp/capacity.json`](/Users/qingpei/.local/state/codex-tmp/capacity.json)
- 当前管理合同：[`bin/TOOLS.md`](/Users/qingpei/git/dotfiles/bin/TOOLS.md#L42-L67)
- 首批 inventory：[`batch-01-results.tsv`](/Users/qingpei/.codex/tmp/codex-tmp-inventory-20260728/batch-01-results.tsv)
- 大型迁移实证：[`closeout.md`](/Users/qingpei/.codex/tmp/cicd-rollout-migration/closeout.md) 与 [`final-validation.md`](/Users/qingpei/.codex/tmp/cicd-rollout-migration/final-validation.md)
- 历史独立审查：[`review.md`](/Users/qingpei/.codex/tmp/codex-tmp-auto-adopt-review-20260728/review.md) 与 [`final-review-after-race-and-framing-fixes.md`](/Users/qingpei/.codex/tmp/codex-tmp-auto-adopt-review-20260728/final-review-after-race-and-framing-fixes.md)
