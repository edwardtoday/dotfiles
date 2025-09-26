#!/usr/bin/env bash

# macOS-specific bootstrap. Exit quietly on other platforms.
[[ ${OSTYPE} == darwin* ]] || exit 0

set -euo pipefail

# Ensure Xcode command line tools are wired up (no sudo switch if already set).
if command -v xcode-select >/dev/null 2>&1; then
  current_path=$(xcode-select -print-path 2>/dev/null || true)
  if [[ -z ${current_path} || ! -d ${current_path} ]]; then
    echo "[osx] Configuring Command Line Tools path"
    sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer 2>/dev/null || \
      sudo xcode-select --switch /Library/Developer/CommandLineTools
  fi
fi

if ! command -v brew >/dev/null 2>&1; then
  cat <<'EOF'
[osx] Homebrew not found. Install manually:
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
EOF
else
  export HOMEBREW_NO_AUTO_UPDATE=1
  export HOMEBREW_NO_ANALYTICS=1

  if [[ -f ${HOME}/.Brewfile ]]; then
    echo "[osx] Checking formulas from ~/.Brewfile"
    if ! brew bundle check --file="${HOME}/.Brewfile" >/dev/null; then
      echo "[osx] Run 'brew bundle install --file=${HOME}/.Brewfile' to sync formulas" >&2
    fi
  fi

  if [[ -x ${HOME}/.cask ]]; then
    echo "[osx] Executing ~/.cask"
    "${HOME}/.cask"
  fi
fi

# Symlink p4merge helper if missing.
if [[ -x ${HOME}/.bin/p4merge.sh ]]; then
  target=/usr/local/bin/p4merge
  if [[ -L ${target} && $(readlink "${target}") == ${HOME}/.bin/p4merge.sh ]]; then
    :
  elif [[ -e ${target} ]]; then
    echo "[osx] Skip linking ${target}: already exists"
  else
    echo "[osx] Linking ${target}"
    sudo ln -s "${HOME}/.bin/p4merge.sh" "${target}"
  fi
fi

if command -v git >/dev/null 2>&1; then
  git config --global credential.helper osxkeychain
fi

# Ensure zsh is the default shell.
if command -v zsh >/dev/null 2>&1; then
  current_shell=$(dscl . -read ~/ UserShell 2>/dev/null | awk '{print $2}')
  if [[ ${current_shell} != /bin/zsh ]]; then
    echo "[osx] Changing default shell to /bin/zsh"
    chsh -s /bin/zsh
  fi
fi
