# edwardtoday’s dotfiles

## Agent Configuration

- `AGENTS.md` 现在只保留全局基线规则，安装脚本会将它软链接为 `~/.AGENTS.md`；低频、专题化规则拆分存放在 `AGENTS.d/`，`~/.codex/AGENTS.md` 等入口文件会统一指向同一套规则。
- 维护规则时，优先把高频、稳定、跨项目的内容放进 `AGENTS.md`，把长篇、专题化或项目特例放进 `AGENTS.d/` 或项目级 `AGENTS.md`；GitLab / MR 约定详见 `AGENTS.d/gitlab.md`。
- 技术指南存放于 `docs/tech-guides/`，默认优先读取本地文件；仅在需要跨仓库引用或外部访问时，再使用对应的 Raw 链接。

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

### Install native apps with `brew cask`

You could also install native apps with [`brew cask`](https://github.com/phinze/homebrew-cask):

```bash
./.cask
```

## Feedback

Suggestions/improvements are [welcome](https://github.com/edwardtoday/dotfiles/issues)!
