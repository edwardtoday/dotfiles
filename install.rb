#!/usr/bin/env ruby

system ("git pull")

# Inspired by http://errtheblog.com/posts/89-huba-huba

# This is idempotent, meaning you can run it over and over again without fear of
# breaking anything. Use it as an installer or to upgrade after merging from an
# upstream fork.

home = File.expand_path('~')

Dir['*'].each do |file|
  next if file =~ /install/ || file =~ /README/
  target = File.join(home, ".#{file}")
  `ln -fns #{File.expand_path file} #{target}`
end

system ("source ~/.init/osx.sh")
system ("source ~/.init/ubuntu.sh")
system ("source ~/.init/fedora.sh")

