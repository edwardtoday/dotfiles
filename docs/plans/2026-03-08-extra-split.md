# 私有 extra 拆分计划

## 目标

- 将原来的 `~/.extra` 拆分为 `~/.extra_env` 与 `~/.extra_login`
- 保持 `~/.extra` 兼容层可用，避免已有手工 `source ~/.extra` 失效
- 修复 `~/.{extra}` 单元素花括号未展开，导致 `extra` 实际未被加载的问题

## 实施步骤

1. 在 `dotfiles-private` 中将原 `extra` 内容迁移到 `extra_env`
2. 将纯环境变量与便携函数保留在 `extra_env`
3. 新建 `extra_login`，放置登录时执行一次的副作用命令
4. 将 `extra` 改为兼容层，转发到 `extra_env` 与 `extra_login`
5. 在 `dotfiles` 中更新 `profile`、`zprofile`、`zshrc`、`bash_profile` 的加载链路
6. 更新 `README.md` 说明新的私有扩展入口

## 验证

- `sh -lc '. ~/.profile >/dev/null'`
- `zsh -ilc 'whence -w set3161; whence -w awsus; alias co'`
- `zsh -ic 'whence -w set3161; whence -w awsus; alias co'`
- `bash -lc 'declare -F set3161; declare -F awsus; alias co'`
- `launchctl getenv CHROME_HEADLESS`
