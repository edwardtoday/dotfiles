# edwardtoday’s dotfiles

## Agent Configuration

- `AGENTS.md` 只保留跨项目、长期稳定且会改变执行结果的用户偏好，安装脚本会将它软链接为 `~/.AGENTS.md`，`~/.codex/AGENTS.md` 等入口文件统一指向同一份基线。
- 专题工作流放在 `~/.agents/skills` 管理的全局 user skills，项目特例放项目级 `AGENTS.md`；`AGENTS.d/` 仅保留不参与自动发现的人工参考资料。
- 技术指南存放于 `docs/tech-guides/`，默认优先读取本地文件；仅在需要跨仓库引用或外部访问时，再使用对应的 Raw 链接。
- `~/.codex/tmp` 只承载跨轮次、跨重启仍需恢复的临时制品；模型优先复用 T7 Git 仓库和共享 Node/Python 环境。`codex-tmp inspect [task]` 只扫描 tmp，并从其中 Git 工作区的脱敏 remote 推导 T7 canonical 迁移目标，不遍历 T7；`codex-tmp recommend [task]` 生成绑定 owner session 的建议包，`codex-tmp clean <recommendation-id>` 只执行已记录且重新验证通过的清理建议。旧的 lifecycle、quarantine 和 restore 命令继续作为兼容与回滚能力，不再是创建临时文件的强制入口。

## Installation

### Using Git and the bootstrap script

You can clone the repository wherever you want. The installation script will symlink the files to your home folder.

```bash
git clone https://github.com/edwardtoday/dotfiles.git && cd dotfiles && ./install.rb
```

To update, `cd` into your local `dotfiles` repository and then:

```bash
./install.rb
```

If a target dot-directory already exists as a real directory instead of a symlink, the installer leaves it in place and prints a skip message so you can migrate it manually.

`~/.codex` is always host-local. The installer never links or replaces its live `config.toml` (Codex and CC Switch edit it). It links the portable `config.common.toml` reference and project-index helper, and creates a private `projects.local.toml` only when missing. Review that file's paths before applying it. On a host without access to the private agent-skills source, use `./install.rb --skip-agent-skills`; core dotfiles initialization still succeeds if the optional skill restore fails.

### Agent skills

[`agents/skills.yml`](agents/skills.yml) retains pinned Git sources and installer provenance. [`agents/skills-runtime.json`](agents/skills-runtime.json) records the exact reviewed runtime content at both personal skill locations, including intentional local overrides. Copies and symlinks are supported; a matching fingerprint does not claim that an unknown upstream source has been verified.

```bash
./bin/agents-skills-audit
./bin/agents-skills-audit --json
./bin/agents-skills-restore --dry-run
./bin/agents-skills-snapshot --skill research
./bin/agents-skills-restore --restore-snapshot research
```

Run `agents-skills-snapshot --skill NAME` only after reviewing and validating your own authorized skill change. Preserve unrelated concurrent drift for its owning task; do not rebaseline it just to make the audit pass. `--all` explicitly records every currently installed personal skill. Snapshot archives live under `~/.local/share/agent-skills/snapshots/`; include that directory with the catalog in configuration backups and host migrations. The catalog alone does not contain the skill bytes. Recording a snapshot verifies content fidelity, not upstream trust or behavioral quality.

With a runtime catalog present, restore recreates missing skills from verified archives and refuses to overwrite existing drift or broken links. It does not fetch or switch source repositories. Without a catalog, the earlier pinned-source restore remains available; dirty source checkouts are preserved, and `--adopt` replaces only identical real directories after backup. `./install.rb` invokes this same restore entrypoint.

### Codex configuration checks

The Lab provider uses the existing `SUB2API_API_KEY` environment variable; keep it available to both terminal and desktop launches. The secret value remains outside tracked configuration. Model defaults, Full Access, and existing production automation authorization are managed separately from this change.

After a configuration update, check strict loading with the installed CLI and desktop binary, inspect the relevant MCP/skill discovery results, and run the focused checks:

```bash
python3 -m unittest discover -s tests -p test_agents_skills_catalog.py
./bin/agents-skills-audit
```

Do not treat parsing, snapshots, or plugin enablement as proof of a successful business operation. Use the task's actual output check. Existing conversations can retain old configuration; verify newly created sessions without restarting active work.

### Ghostty

Ghostty is managed from `config/ghostty/config.ghostty` and will be symlinked to `~/.config/ghostty/config.ghostty` by `./install.rb`.

The current profile is tuned for macOS and uses Catppuccin light/dark theme switching, translucent background blur, a Quake-style quick terminal, and custom split/tab keybindings. It prefers `Maple Mono NF CN` and falls back to `MesloLGS NF` if Maple is not installed.

### Add custom commands without creating a new fork

If `~/.extra_env` exists, it is sourced from the shell-agnostic profile and zsh interactive startup. Use it for private environment variables and portable helper functions you don’t want to commit to the public repository.

If `~/.extra_login` exists, it is sourced only by login shells. Use it for login-time commands such as `git config`, `launchctl`, or shell integrations that should not run on every profile load.

`~/.extra` is kept as a compatibility shim in my private setup, but new customizations should go into `~/.extra_env` or `~/.extra_login` instead.

My login-only private config looks something like this:

```bash
# Git credentials
# Not in the repository, to prevent people from accidentally committing under my name
git config --global user.name "Pei Qing 卿培"
git config --global user.email "edwardtoday@gmail.com"
```

You could also use `~/.extra_env` to override settings or add helper functions on top of this repository. It’s probably better to [fork this repository](https://github.com/edwardtoday/dotfiles/fork) instead, though.

For example, keep private service credentials in `~/.extra_env`, such as `IMMICH_URL`, `IMMICH_QP_KEY`, `IMMICH_ZXF_KEY`, `IMMICH_QHY_KEY`, and `IMMICH_LJH_KEY`, so the public repo only contains Immich commands that reference those variables.

### Zsh prompt

Interactive `zsh` now uses [`starship`](https://starship.rs/) for prompt rendering and no longer depends on loading the `oh-my-zsh` framework during startup.

`./install.rb` will symlink [`config/starship.toml`](config/starship.toml) to `~/.config/starship.toml`. Install the binary with `brew bundle ~/.Brewfile` or `brew install starship`.

The shell still keeps `zsh-autocomplete`, `atuin`, `zoxide`, `zsh-autosuggestions`, and `zsh-syntax-highlighting`, plus a small compatibility layer for the most-used old `oh-my-zsh` aliases and helper functions. `compinit` is now owned by `zsh-autocomplete`; avoid adding a second manual `compinit` block in `~/.zshrc`.

### Validate shell startup

Run `~/.bin/shell-startup-smoke-check` (or `./bin/shell-startup-smoke-check` inside the repo) to verify `zsh -ilc`, `zsh -ic`, and `bash -lc` all expose `SR_BASE_URL`, `set3161`, `awsus`, and `co`.

Use `./bin/test-shell-startup-smoke-check` to run the fixture-based regression check for the smoke command itself.

### Sensible OS X defaults

When setting up a new Mac, you may want to set some sensible OS X defaults:

```bash
./osx
```

Or if you have already run the `install.rb` script,

```bash
~/.osx
```

### Install Homebrew formulae

When setting up a new Mac, you may want to install some common [Homebrew](http://brew.sh/) formulae (after installing Homebrew, of course):

```bash
brew bundle ~/.Brewfile
```

### Rebuild an excluded developer environment

Time Machine intentionally excludes package-manager installations, language caches,
virtual environments, Xcode, and MacTeX that can be recreated from versioned
manifests. Follow [`docs/environment-rebuild.md`](docs/environment-rebuild.md) after
restoring this repository. The canonical Homebrew inventory remains `Brewfile`, and
Conda/tool manifests live under `docs/rebuild/`.

### Install native apps with `brew cask`

You could also install native apps with [`brew cask`](https://github.com/phinze/homebrew-cask):

```bash
./.cask
```

## Feedback

Suggestions/improvements are [welcome](https://github.com/edwardtoday/dotfiles/issues)!
