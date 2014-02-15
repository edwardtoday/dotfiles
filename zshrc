source ~/.zprofile

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
if uname -s | grep -q Darwin
then
	plugins=(command-coloring autojump osx brew bower git-extras git-flow python scala pip dirpersist history history-substring-search terminalapp ruby gem)
else
	# Not on mac, using ssh-agent plugin
	plugins=(command-coloring ssh-agent dirpersist git-extras git-flow history history-substring-search)
fi

source $ZSH/oh-my-zsh.sh

bindkey ' ' magic-space
bindkey '^[^[[D' backward-word
bindkey '^[^[[C' forward-word
bindkey '^[[5D' beginning-of-line
bindkey '^[[5C' end-of-line
bindkey '^[[3~' delete-char
bindkey '^[^N' newtab
bindkey '^?' backward-delete-char

# Add the following to your zshrc to access the online help:
autoload run-help
HELPDIR=/usr/local/share/zsh/helpfiles

# added by travis gem
[ -f /home/qingpei/.travis/travis.sh ] && source /home/qingpei/.travis/travis.sh

# completion
autoload -U compinit
compinit

autoload colors && colors
