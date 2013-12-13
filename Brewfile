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
install grep

install screen

# Install other useful binaries
install ack
#install exiv2
install git
#install imagemagick
install lynx
install node
install pigz
install rename
install rhino
install tree
install webkit2png

# previously installed
install aacgain
install apple-gcc42
install asciidoc
install aspell
install astyle
install atk
install autoconf
install autojump
install automake
install bash
install boost
install brew-cask
install cairo
install celt
install cloog
install cmake
install coreutils
install cscope
install curl
install curl-ca-bundle
install d-bus
install discount
install ditaa
install docbook
install docbook-xsl
install doxygen
install emacs
install faac
install fdk-aac
install ffmpeg
install findutils
install fontconfig
install fontforge
install fop
install freetype
install fribidi
install fuse4x
install fuse4x-kext
install gd
install gdbm
install gdk-pixbuf
install gettext
install gfortran
install gist
install git
install git-extras
install git-flow
install glib
install gmp
install gnu-getopt
install gnuplot
install gnutls
install go
install gobject-introspection
install graphviz
install grc
install gtk+
install harfbuzz
install hevea
install icu4c
install imagemagick
install isl
install jasper
install jpeg
install jpegoptim
install kindlegen
install lame
install latex2rtf
install libass
install libffi
install libgcrypt
install libgpg-error
install libmpc
install libogg
install libpng
install libsvg
install libsvg-cairo
install libtasn1
install libtiff
install libtool
install libvo-aacenc
install libvorbis
install libvpx
install libyaml
install little-cms2
install lua
install mercurial
install mobile-shell
install mp3gain
install mpfr
install netpbm
install nettle
install node
install ntfs-3g
install objective-caml
install opencc
install opencore-amr
install openjpeg
install openssl
install opus
install orc
install osxutils
install p11-kit
install p7zip
install pango
install parallel
install pcre
install pdf2htmlex
install pixman
install pkg-config
install pngcrush
install poppler
install protobuf
install python
install python3
install qpdf
install qtfaststart
install readline
install ruby
install schroedinger
install scons
install sdl
install serf
install shtool
install source-highlight
install speex
install sqlite
install ssh-copy-id
install svg2pdf
install svg2png
install theora
install tree
install ttfautohint
install webkit2png
install wget
install x264
install xmlto
install xvid
install xz
install yasm
install youtube-dl
install yuicompressor
install z
install zsh
install zsh-completions
install zsh-lovers
install zsh-syntax-highlighting

linkapps
# Remove outdated versions from the cellar
cleanup
prune

# Install Brew Cask
tap phinze/homebrew-cask
install brew-cask

cask install google-chrome
cask install calibre
cask install ksdiff
cask install p4merge
cask install pandoc
