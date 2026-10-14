[ -r ~/.extra_env ] && [ -f ~/.extra_env ] && source ~/.extra_env

# 非 login 的交互式 zsh 也需要尽早看见 Homebrew 可执行文件，方便初始化插件。
export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:$PATH"
export PATH="/opt/homebrew/opt/imagemagick-full/bin:$PATH"

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
bindkey -M viins "^K" kill-line

# Prefer Homebrew Ruby over system Ruby
export PATH="/opt/homebrew/opt/ruby/bin:$PATH"
# Add user-installed gem executables to PATH for Homebrew Ruby
export GEM_HOME="${GEM_HOME:-/opt/homebrew/lib/ruby/gems/$(/opt/homebrew/opt/ruby/bin/ruby -e 'print RbConfig::CONFIG["ruby_version"]')}"
# 防止历史环境里残留的尾随空格污染 PATH（如 "...gems/4.x.x /bin"）
GEM_HOME="${GEM_HOME%"${GEM_HOME##*[![:space:]]}"}"
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

# bun completions
[ -s "$HOME/.bun/_bun" ] && source "$HOME/.bun/_bun"

# bun
export BUN_INSTALL="$HOME/.bun"
export PATH="$BUN_INSTALL/bin:$PATH"

# 31233 SOCKS5 -> 127.0.0.1:1081
start-31233-socks5-1081() {
  if lsof -nP -iTCP:1081 -sTCP:LISTEN >/dev/null 2>&1; then
    echo "socks5 already listening on 127.0.0.1:1081"
    return 0
  fi
  ssh -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=2 -fN -D 127.0.0.1:1081 31233
  if lsof -nP -iTCP:1081 -sTCP:LISTEN >/dev/null 2>&1; then
    echo "socks5 started on 127.0.0.1:1081"
    return 0
  fi
  echo "failed to start socks5 on 127.0.0.1:1081" >&2
  return 1
}

stop-31233-socks5-1081() {
  local pid
  pid=$(lsof -t -iTCP:1081 -sTCP:LISTEN 2>/dev/null || true)
  if [ -z "$pid" ]; then
    echo "socks5 not running on 127.0.0.1:1081"
    return 0
  fi
  kill "$pid"
  sleep 0.2
  if lsof -nP -iTCP:1081 -sTCP:LISTEN >/dev/null 2>&1; then
    echo "failed to stop socks5 on 127.0.0.1:1081" >&2
    return 1
  fi
  echo "socks5 stopped on 127.0.0.1:1081"
}

# pnpm
export PNPM_HOME="$HOME/Library/pnpm"
case ":$PATH:" in
  *":$PNPM_HOME/bin:"*) ;;
  *) export PATH="$PNPM_HOME/bin:$PATH" ;;
esac
# pnpm end

# AsyncAPI CLI Autocomplete

ASYNCAPI_AC_ZSH_SETUP_PATH="$HOME/Library/Caches/@asyncapi/cli/autocomplete/zsh_setup"
test -f "$ASYNCAPI_AC_ZSH_SETUP_PATH" && source "$ASYNCAPI_AC_ZSH_SETUP_PATH"; # asyncapi autocomplete setup
