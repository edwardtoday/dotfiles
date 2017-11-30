# edwardtoday’s dotfiles

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

