##############################################################################
# Import the shell-agnostic (Bash or Zsh) environment config
##############################################################################
source ~/.profile

##############################################################################
# ZShell History Configuration
##############################################################################

HISTFILE=~/.zsh_history     # Where to save history to disk
setopt APPEND_HISTORY # adds history
setopt AUTO_CONTINUE     # Background processes aren't killed on exit of shell
setopt COMPLETE_IN_WORD
setopt CORRECT
setopt correctall        # correction
setopt EXTENDED_HISTORY # add timestamps to history
setopt extendedglob
setopt HIST_IGNORE_ALL_DUPS  # don't record dupes in history
setopt HIST_REDUCE_BLANKS
setopt HIST_VERIFY
setopt IGNORE_EOF
setopt INC_APPEND_HISTORY SHARE_HISTORY  # adds history incrementally and share it across sessions
setopt LOCAL_OPTIONS # allow functions to have local options
setopt LOCAL_TRAPS # allow functions to have local traps
setopt NO_BG_NICE # don't nice background tasks
setopt NO_HUP
setopt NO_LIST_BEEP
setopt PROMPT_SUBST
setopt RM_STAR_WAIT      # prompts for confirmation after 'rm *' etc

# don't expand aliases _before_ completion has finished
#   like: git comm-[tab]
setopt complete_aliases

zle -N newtab

# for mactex
eval `/usr/libexec/path_helper -s`

export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"