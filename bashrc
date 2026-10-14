#!/bin/bash

########################################################################
# Bash non-interactive session setup
########################################################################

# Bash non-interactive shell will load the same functions as the interactive shell
source ~/.bash_profile

PATH=$PATH:$HOME/.rvm/bin # Add RVM to PATH for scripting

# added by travis gem
[ -f "$HOME/.travis/travis.sh" ] && source "$HOME/.travis/travis.sh"

[ -r "$HOME/.config/broot/launcher/bash/br" ] && source "$HOME/.config/broot/launcher/bash/br"

[ -f ~/.fzf.bash ] && source ~/.fzf.bash

# Added by LM Studio CLI (lms)
export PATH="$PATH:$HOME/.lmstudio/bin"

# AsyncAPI CLI Autocomplete

ASYNCAPI_AC_BASH_SETUP_PATH="$HOME/Library/Caches/@asyncapi/cli/autocomplete/bash_setup"
test -f "$ASYNCAPI_AC_BASH_SETUP_PATH" && source "$ASYNCAPI_AC_BASH_SETUP_PATH"; # asyncapi autocomplete setup
