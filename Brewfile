# Install Homebrew with:
#  ruby -e "$(curl -fsSL https://raw.github.com/mxcl/homebrew/go/install)"
# Install Homebrew formulae with:
#  brew bundle ~/.Brewfile

# Make sure we’re using the latest Homebrew
update

# Upgrade any already-installed formulae
upgrade

# Install GNU core utilities (those that come with OS X are outdated)
# Don’t forget to add `$(brew --prefix coreutils)/libexec/gnubin` to `$PATH`.
install coreutils
# Install GNU `find`, `locate`, `updatedb`, and `xargs`, g-prefixed
install findutils
# Install Bash 4
install bash

# Install wget with IRI support
install wget --enable-iri

# Install RingoJS and Narwhal
# Note that the order in which these are installed is important; see http://git.io/brew-narwhal-ringo.
#install ringojs
#install narwhal

# Install more recent versions of some OS X tools
install vim --override-system-vi --with-python3 --with-perl --with-tcl --with-client-server
install macvim --custom-icons --override-system-vim --with-python3
tap homebrew/dupes
install homebrew/dupes/grep
tap josegonzalez/homebrew-php
# install php55

# This formula didn’t work well last time I tried it:
#install homebrew/dupes/screen

# Install other useful binaries
install ack
#install exiv2
install git
#install imagemagick
install lynx
install node
install pandoc
install pigz
install rename
install rhino
install tree
install webkit2png
install zopfli

tap homebrew/versions
#install lua52

# Remove outdated versions from the cellar
cleanup

# Install Brew Cask
tap phinze/homebrew-cask
install brew-cask

cask install google-chrome
cask install calibre
cask install ksdiff
cask install p4merge