# Ubuntu-only stuff. Abort if not Fedora.
[[ "$(cat /etc/issue 2> /dev/null)" =~ Fedora ]] || return 1

