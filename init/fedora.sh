# Ubuntu-only stuff. Abort if not Fedora.
[[ "$(cat /etc/issue 2> /dev/null)" =~ Fedora ]] || return 1

# Update YUM.
echo "Updating YUM"
sudo yum update
sudo yum upgrade
sudo yum install -y 
