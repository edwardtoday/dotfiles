[ -r ~/.extra_env ] && [ -f ~/.extra_env ] && source ~/.extra_env

# 非 login 的交互式 zsh 也需要尽早看见 Homebrew 可执行文件，方便初始化插件。
export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:$PATH"

if [ -d /opt/homebrew/share/zsh/site-functions ]; then
  fpath=(/opt/homebrew/share/zsh/site-functions $fpath)
fi

if [ -d "$HOME/.docker/completions" ]; then
  fpath=("$HOME/.docker/completions" $fpath)
fi

# 复用 host 维度的 compdump，避免每个交互式 shell 都重新扫描补全定义。
if [[ "$OSTYPE" == darwin* ]]; then
  local_host_name="$(scutil --get LocalHostName 2>/dev/null || print -r -- "${HOST%%.*}")"
else
  local_host_name="${HOST%%.*}"
fi

ZSH_COMPDUMP="${ZDOTDIR:-$HOME}/.zcompdump-${local_host_name}-${ZSH_VERSION}"
zstyle ':autocomplete::compinit' arguments -C -i

# zsh-autocomplete 官方建议由它自己接管 compinit，这里只提前给出 dump 路径与参数。
[ -r /opt/homebrew/share/zsh-autocomplete/zsh-autocomplete.plugin.zsh ] && source /opt/homebrew/share/zsh-autocomplete/zsh-autocomplete.plugin.zsh

autoload -Uz add-zsh-hook
_zshrc_compile_compdump_once() {
  add-zsh-hook -d precmd _zshrc_compile_compdump_once
  if [[ -s "$ZSH_COMPDUMP" ]] && { [[ ! -s "$ZSH_COMPDUMP.zwc" ]] || [[ "$ZSH_COMPDUMP" -nt "$ZSH_COMPDUMP.zwc" ]]; }; then
    (zcompile "$ZSH_COMPDUMP" 2>/dev/null) &!
  fi
}
add-zsh-hook precmd _zshrc_compile_compdump_once
unset local_host_name

for file in ~/.{shellaliases,shellfuncs}; do
  [ -r "$file" ] && [ -f "$file" ] && source "$file"
done
unset file

if command -v pip3 >/dev/null 2>&1 && ! command -v pip >/dev/null 2>&1; then
  alias pip='noglob pip3'
fi

if (( $+functions[compdef] )); then
  compdef _tmux ta tad to ts tkss
  compdef _pip pipig pipigb pipigp
fi

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

command -v atuin >/dev/null && eval "$(atuin init zsh --disable-up-arrow --disable-ai)"
command -v zoxide >/dev/null && eval "$(zoxide init zsh)"

if command -v starship >/dev/null 2>&1; then
  eval "$(starship init zsh)"
elif [ -x /opt/homebrew/bin/starship ]; then
  eval "$(/opt/homebrew/bin/starship init zsh)"
else
  PROMPT='%F{green}%n@%m%f %B%F{blue}%~%f%b
%# '
  RPROMPT=
fi

[ -r /opt/homebrew/share/zsh-autosuggestions/zsh-autosuggestions.zsh ] && source /opt/homebrew/share/zsh-autosuggestions/zsh-autosuggestions.zsh
[ -r /opt/homebrew/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh ] && source /opt/homebrew/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
