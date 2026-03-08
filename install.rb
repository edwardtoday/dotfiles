#!/usr/bin/env ruby

require 'fileutils'

# Inspired by http://errtheblog.com/posts/89-huba-huba
#
# This is idempotent, meaning you can run it over and over again without fear of
# breaking anything. Use it as an installer or to upgrade after merging from an
# upstream fork.

home = File.expand_path('~')
repo_root = File.expand_path(File.dirname(__FILE__))

run_bootstrap = ARGV.delete('--bootstrap')

def ensure_symlink(source, target)
  if File.symlink?(target)
    FileUtils.rm_f(target)
  elsif File.directory?(target)
    puts "[install] skip #{target}: exists and is not a symlink"
    return
  end

  FileUtils.ln_sf(source, target)
end

Dir['*'].each do |file|
  next if file =~ /install/ || file =~ /README/ || file == 'config'

  source = File.expand_path(file, repo_root)
  target = File.join(home, ".#{file}")
  ensure_symlink(source, target)
end

config_src = File.join(repo_root, 'config')
if File.directory?(config_src)
  config_target_dir = File.join(home, '.config')
  FileUtils.mkdir_p(config_target_dir)

  obsolete = File.join(config_target_dir, 'config')
  if File.symlink?(obsolete) && File.readlink(obsolete) == config_src
    FileUtils.rm(obsolete)
  end

  Dir.children(config_src).each do |entry|
    next if entry.start_with?('.')

    source = File.join(config_src, entry)
    target = File.join(config_target_dir, entry)

    ensure_symlink(source, target)
  end
end

init_dir = File.join(home, '.init')
if run_bootstrap && File.directory?(init_dir)
  %w[osx ubuntu fedora].each do |name|
    script = File.join(init_dir, "#{name}.sh")
    next unless File.executable?(script)

    puts "[install] running #{script}"
    system(script)
  end
elsif File.directory?(init_dir)
  puts "[install] skipping OS bootstrap scripts; run with --bootstrap or execute ~/.init/*.sh manually"
end
