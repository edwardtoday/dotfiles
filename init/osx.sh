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

# Link Homebrew casks in `/Applications` rather than `~/Applications`
export HOMEBREW_CASK_OPTS="--appdir=/Applications"

if [[ "$(type -P brew)" ]]; then
  echo "Updating Homebrew"

  brew bundle ~/.Brewfile

  # This is where brew stores its binary symlinks
  local binroot="$(brew --config | awk '/HOMEBREW_PREFIX/ {print $2}')"/bin

  # htop
  if [[ "$(type -P $binroot/htop)" && "$(stat -L -f "%Su:%Sg" "$binroot/htop")" != "root:wheel" || ! "$(($(stat -L -f "%DMp" "$binroot/htop") & 4))" ]]; then
    echo "Updating htop permissions"
    sudo chown root:wheel "$binroot/htop"
    sudo chmod u+s "$binroot/htop"
  fi

  # bash
#  if [[ "$(type -P $binroot/bash)" && "$(cat /etc/shells | grep -q "$binroot/bash")" ]]; then
#    echo "Adding $binroot/bash to the list of acceptable shells"
#    echo "$binroot/bash" | sudo tee -a /etc/shells >/dev/null
#  fi
#  if [[ "$SHELL" != "$binroot/bash" ]]; then
#    echo "Making $binroot/bash your default shell"
#    sudo chsh -s "$binroot/bash" "$USER" >/dev/null 2>&1
#    e_arrow "Please exit and restart all your shells."
#  fi

  # i don't remember why i needed this?!
#  if [[ ! "$(type -P gcc-4.2)" ]]; then
#    echo "Installing Homebrew dupe recipe: apple-gcc42"
#    brew install https://raw.github.com/Homebrew/homebrew-dupes/master/apple-gcc42.rb
#  fi
fi
