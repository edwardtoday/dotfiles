#!/bin/bash

########################################################################
# Bash non-interactive session setup
########################################################################

# Bash non-interactive shell will load the same functions as the interactive shell
source ~/.bash_profile

PATH=$PATH:$HOME/.rvm/bin # Add RVM to PATH for scripting

# added by travis gem
[ -f /home/qingpei/.travis/travis.sh ] && source /home/qingpei/.travis/travis.sh
