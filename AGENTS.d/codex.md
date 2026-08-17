# Codex 专用约定

仅当任务涉及 Codex CLI、Codex Desktop、Codex 配置或独立 Codex 审查时，才读取本文件。

## 独立审查的配置与认证

- 启动独立只读 Codex 审查时，默认保留 `~/.codex/config.toml`，不得例行添加 `--ignore-user-config`。
- `--ignore-user-config` 会跳过用户配置中的 provider、endpoint、model 等路由信息；在自定义 provider 环境中可能使进程落到错误的连接或凭证组合并返回 401。
- 只有任务明确要求验证无用户配置的基线行为，并且已单独确认目标 provider、endpoint 与认证来源时，才允许使用该参数；失败时不得据此判断 Codex Desktop 登录失效或待审实现有问题。
- 隔离独立审查优先使用 `--ephemeral`、`--ignore-rules` 和 `-s read-only`，不要通过丢弃正常 provider 配置来制造隔离。
