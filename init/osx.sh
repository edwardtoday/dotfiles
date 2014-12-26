#/usr/bin/env sh

# OSX-only stuff. Abort if not OSX.
[[ "$OSTYPE" =~ ^darwin ]] || return 1

# Some tools look for XCode, even though they don't need it.
# https://github.com/joyent/node/issues/3681
# https://github.com/mxcl/homebrew/issues/10245
if [[ ! -d "$('xcode-select' -print-path 2>/dev/null)" ]]; then
  sudo xcode-select -switch /usr/bin
fi

# Install Homebrew.
if [[ ! "$(type -P brew)" ]]; then
  echo "Installing Homebrew"
  true | ruby -e "$(curl -fsSL https://raw.github.com/mxcl/homebrew/go/install)"
fi

# Install Homebrew Cask

if [[ "$(type -P brew)" ]]; then
  sh ~/.cask
fi

# Link Homebrew casks in `/Applications` rather than `~/Applications`
export HOMEBREW_CASK_OPTS="--appdir=/Applications"

if [[ "$(type -P brew)" ]]; then
  brew install $(cat ~/.Brewfile|grep -v "#")
fi

ln -s ~/.bin/p4merge.sh /usr/local/bin/p4merge

# Use Keychain for git auth
git config --global credential.helper osxkeychain

# Install oh-my-zsh
curl -L http://install.ohmyz.sh | sh

# change default shell to zsh
chsh -s /bin/zsh

# Install Alcatraz | The Package manager for XCode
curl -fsSL https://raw.github.com/supermarin/Alcatraz/master/Scripts/install.sh | sh