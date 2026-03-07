# GitLab 约定与访问（扩展）

仅当任务涉及 GitLab、Merge Request、Issue 评论、描述更新或私有 GitLab 检索时，才读取本文件。

## 1. Merge Request 约定

- 新建 Merge Request 时，默认添加 `Draft: ` 前缀。
- 在 pipeline 全部通过、日志检查无误且确认无合并冲突后，再移除 `Draft: ` 前缀。

## 2. GitLab CLI / API 多行正文规范

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

## 3. 公司私有 GitLab 访问

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
