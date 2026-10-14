# The following lines were added by Docker Desktop to add commands to your PATH.
export PATH="$PATH:$HOME/.docker/bin"
# End of Docker Desktop section.

#############################################################
# Generic configuration that applies to all shells
#############################################################

###################
# Load only shell-agnostic dotfiles here.
# Shell-specific aliases/functions/prompt should be loaded from the
# corresponding shell startup files instead of this generic profile.
for file in ~/.{shellpaths,shellvars,extra_env}; do
	        [ -r "$file" ] && [ -f "$file" ] && source "$file"
done
unset file

# Added by LM Studio CLI (lms)
export PATH="$PATH:$HOME/.lmstudio/bin"
