# edwardtoday’s dotfiles

## Agent Configuration

- `AGENTS.md` 记录了个人 Coding Agent 的核心协议，安装脚本会将它软链接为 `~/.AGENTS.md`（以及 `.codex/AGENTS.md` 等依赖文件）。
- 更新该文件时默认遵循文档中的自动阶段转换规则；提交 Merge Request 时请先以 `Draft:` 前缀创建，待 CI 管道全部通过、日志核对完毕且确认无冲突后再去除前缀。
- 技术指南拆分存放于 `docs/tech-guides/`，如需查阅请直接访问当前分支 (`osx`) 下的 raw 链接，无需默认纳入上下文。

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

