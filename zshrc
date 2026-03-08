[ -r ~/.extra_env ] && [ -f ~/.extra_env ] && source ~/.extra_env

for file in ~/.{shellaliases,shellfuncs,prompt}; do
  [ -r "$file" ] && [ -f "$file" ] && source "$file"
done
unset file

# Path to your oh-my-zsh configuration.
ZSH=$HOME/.oh-my-zsh

# Set name of the theme to load.
# Look in ~/.oh-my-zsh/themes/
# Optionally, if you set this to "random", it'll load a random theme each
# time that oh-my-zsh is loaded.
#ZSH_THEME="robbyrussell" # amuse, bira, ys
ZSH_THEME="bira"

# Set to this to use case-sensitive completion
# CASE_SENSITIVE="true"

# Comment this out to disable bi-weekly auto-update checks
# DISABLE_AUTO_UPDATE="true"

# Uncomment to change how many often would you like to wait before auto-updates occur? (in days)
export UPDATE_ZSH_DAYS=13
DISABLE_UPDATE_PROMPT=true

# Uncomment following line if you want to disable colors in ls
# DISABLE_LS_COLORS="true"

# Uncomment following line if you want to disable autosetting terminal title.
# DISABLE_AUTO_TITLE="true"

# Uncomment following line if you want red dots to be displayed while waiting for completion
# COMPLETION_WAITING_DOTS="true"

# Uncomment following line if you want to disable marking untracked files under
# VCS as dirty. This makes repository status check for large repositories much,
# much faster.
DISABLE_UNTRACKED_FILES_DIRTY="true"

# Which plugins would you like to load? (plugins can be found in ~/.oh-my-zsh/plugins/*)
# Custom plugins may be added to ~/.oh-my-zsh/custom/plugins/
# Example format: plugins=(rails git textmate ruby lighthouse)
if uname -s | grep -q Darwin; then
	plugins=(autojump macos brew github gitignore python pip history ruby gem gnu-utils rsync colorize sublime mosh npm tmux)
else
	# Not on mac, using ssh-agent plugin
	plugins=(command-coloring ssh-agent git-extras git-flow history tmux)
fi

source $ZSH/oh-my-zsh.sh

# The following lines have been added by Docker Desktop to enable Docker CLI completions.
fpath=(/Users/qingpei/.docker/completions $fpath)
# completion
autoload -U compinit
compinit
# End of Docker CLI completions

autoload colors && colors

bindkey ' ' magic-space
bindkey "^A" vi-beginning-of-line
bindkey "^E" vi-end-of-line

# Prefer Homebrew Ruby over system Ruby
export PATH="/opt/homebrew/opt/ruby/bin:$PATH"
# Add user-installed gem executables to PATH for Homebrew Ruby
export GEM_HOME="${GEM_HOME:-/opt/homebrew/lib/ruby/gems/$(/opt/homebrew/opt/ruby/bin/ruby -e 'print RbConfig::CONFIG["ruby_version"]') }"
export PATH="$GEM_HOME/bin:$PATH"
# Use user-level prefix for global npm installs
export NPM_CONFIG_PREFIX="$HOME/.npm-global"
export PATH="$HOME/.npm-global/bin:$PATH"

# Go tools (go install)
export PATH="$HOME/go/bin:$PATH"

# Prefer Homebrew sqlite for local dev
export PATH="/opt/homebrew/opt/sqlite/bin:$PATH"
