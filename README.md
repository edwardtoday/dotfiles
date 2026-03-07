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

### Add custom commands without creating a new fork

If `~/.extra` exists, it will be sourced along with the other files. You can use this to add a few custom commands without the need to fork this entire repository, or to add commands you don’t want to commit to a public repository.

My `~/.extra` looks something like this:

```bash
# Git credentials
# Not in the repository, to prevent people from accidentally committing under my name
git config --global user.name "Pei Qing 卿培"
git config --global user.email "edwardtoday@gmail.com"
```

You could also use `~/.extra` to override settings, functions and aliases from my dotfiles repository. It’s probably better to [fork this repository](https://github.com/edwardtoday/dotfiles/fork) instead, though.

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

