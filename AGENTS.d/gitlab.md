# GitLab 约定与访问（扩展）

仅当任务涉及 GitLab、Merge Request、Issue 评论、描述更新或私有 GitLab 检索时，才读取本文件。

## 1. Sansi 本地仓库复用

- 处理 `git.sansi.net` 项目前，先确认 `/Volumes/T7/git-sansi` 已挂载，并用目标 remote URL 在该目录查找同源仓库。
- 同源仓库存在时，优先在原仓库 fetch 后切换或更新目标分支；需要隔离并发修改时，从该仓库创建 `git worktree`，不要重复完整 clone。
- T7 没有同源仓库但任务仍需要本地副本时，首选在 `/Volumes/T7/git-sansi` 下对应的 canonical path clone；只有 T7 不可用或该路径不能满足任务时，才选择其他临时位置，并在 session 中说明原因。
- 本地测试生成的 Cargo `target`、`node_modules`、`dist`、coverage 等可再生大目录不属于恢复证据；验收完成后立即删除，或使用有明确清理策略的共享缓存。

## 2. Merge Request 约定

- 新建 Merge Request 时，默认添加 `Draft: ` 前缀。
- 在 pipeline 全部通过、日志检查无误、确认无合并冲突，并满足本轮明确的 review gate 后，再移除 `Draft: ` 前缀；若目标是保留给真人 reviewer 判断，可以继续保持 Draft。

### Review gate 判定

- 不全局预设必须真人批准、bot 接受即可放行，或真人批准可以覆盖 bot 拒绝；每次任务都应根据用户要求、项目规则和当前 MR 状态明确本轮 review gate。
- GitLab approvals API 的 `approved=true` 在项目 `approvals_required=0` 时是空值恒真，只能证明项目当前不要求 approval，不能证明真人或 bot 已完成审阅；需要哪类审阅证据，按本轮 review gate 单独核对。
- Ready 或 merge 前至少核对：非 Draft、head pipeline 与当前 SHA 匹配且通过、无合并冲突、无未妥善处理的阻塞讨论，并满足本轮明确的 review gate。
- 真人和 bot 的负面意见都应逐条判断：成立则修复并请求复评，不成立则用证据回复；不得仅凭另一方的正面结论静默忽略未处理的有效问题。

## 3. GitLab CLI / API 多行正文规范

### 目标

避免在 GitLab 评论或描述中出现可见的字面 `\n`，而不是实际换行。

### 核心规则

1. 任何包含换行的 `body` / `description`，都不应在命令中直接内联长字符串。
2. 默认推荐“先写文件，再读取文件内容提交”的方式构造正文。
3. 发送后应立刻回读校验；若发现字面 `\n`，应立即编辑修正。

### 默认推荐做法

```bash
cat > /tmp/gitlab_body.md <<'EOF'
第一行

第二行
- 列表项 A
- 列表项 B
EOF

# Issue 评论
glab issue comment <iid> --repo <group/project> --message "$(cat /tmp/gitlab_body.md)"

# MR 描述更新
glab mr update <iid> --repo <group/project> -d "$(cat /tmp/gitlab_body.md)" --yes

# 或 API（note/body / description 同理）
glab api -X PUT "projects/<urlencoded_path>/issues/<iid>/notes/<note_id>" \
  -F body="$(cat /tmp/gitlab_body.md)"
```

### 回读校验

```bash
glab issue view <iid> --repo <group/project> --comments
# 或
glab mr view <iid> --repo <group/project> --comments
```

若输出里仍有可见 `\n`，说明正文构造方式有误，应先修复后再继续。

## 4. 公司私有 GitLab 访问

当需要访问公司私有 GitLab API 时，统一通过环境变量令牌访问。

- 目标域：`https://git.sansi.net:6101`
- 访问令牌：`$GITLAB_TOKEN`（建议 scope：`read_api`，必要时 `api`）
- 使用约定：所有 GitLab API 请求均应携带 `PRIVATE-TOKEN: $GITLAB_TOKEN` 请求头。

### 典型用法

- 获取组 ID：`GET /api/v4/groups?search=sr_pro`
- 组级代码搜索：`GET /api/v4/groups/<GROUP_ID>/search?scope=blobs&search=<query>`
- 拉取命中文件：`GET /api/v4/projects/<PROJECT_ID>/repository/files/<urlencoded_path>/raw?ref=<REF>`

### 安全要求

- 令牌只通过环境变量注入，不写入仓库或日志。
- 权限遵循最小化原则，并定期轮换。
- 本地与 CI 统一读取 `$GITLAB_TOKEN`。
