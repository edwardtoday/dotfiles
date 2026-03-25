# for mactex
eval $(/usr/libexec/path_helper -s)

##############################################################################
# Import the shell-agnostic (Bash or Zsh) environment config
##############################################################################
source ~/.profile

[ -r ~/.extra_login ] && [ -f ~/.extra_login ] && source ~/.extra_login

if [[ -o interactive ]]; then
  ##############################################################################
  # Interactive shell behavior
  ##############################################################################

  HISTFILE=~/.zsh_history # Where to save history to disk
  setopt APPEND_HISTORY   # adds history
  setopt AUTO_CONTINUE    # Background processes aren't killed on exit of shell
  setopt COMPLETE_IN_WORD
  setopt CORRECT
  setopt EXTENDED_HISTORY # add timestamps to history
  setopt HIST_IGNORE_ALL_DUPS # don't record dupes in history
  setopt HIST_REDUCE_BLANKS
  setopt HIST_VERIFY
  setopt IGNORE_EOF
  setopt INC_APPEND_HISTORY SHARE_HISTORY # adds history incrementally and share it across sessions
  setopt LOCAL_OPTIONS                    # allow functions to have local options
  setopt LOCAL_TRAPS                      # allow functions to have local traps
  setopt NO_BG_NICE                       # don't nice background tasks
  setopt NO_HUP
  setopt NO_LIST_BEEP
  setopt PROMPT_SUBST
  setopt RM_STAR_WAIT # prompts for confirmation after 'rm *' etc

  # don't expand aliases _before_ completion has finished
  #   like: git comm-[tab]
  setopt complete_aliases

  typeset -f newtab >/dev/null 2>&1 && zle -N newtab
  [ -r /opt/homebrew/opt/autoenv/activate.sh ] && source /opt/homebrew/opt/autoenv/activate.sh
fi

# Prefer Homebrew Ruby for login shells as well
export PATH="/opt/homebrew/opt/ruby/bin:$PATH"
export GEM_HOME="${GEM_HOME:-/opt/homebrew/lib/ruby/gems/$(/opt/homebrew/opt/ruby/bin/ruby -e 'print RbConfig::CONFIG["ruby_version"]') }"
export PATH="$GEM_HOME/bin:$PATH"
export PATH="$HOME/.cargo/bin:$PATH"
export PATH="$HOME/.rustup/toolchains/stable-aarch64-apple-darwin/bin:$PATH"

# PATH de-dup and prune for login shells
if [ -n "$PATH" ]; then
  typeset -Ua _p
  typeset -a deduped
  typeset seen=""
  _p=(${(s/:/)PATH})
  for d in "${_p[@]}"; do
    [[ -d "$d" ]] || continue
    case ":$seen:" in *:"$d":*) continue;; esac
    seen="$seen:$d"
    deduped+="$d"
  done
  export PATH="${(j/:/)deduped}"
  unset _p deduped seen
fi
