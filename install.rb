#!/usr/bin/env ruby

require 'fileutils'

# Inspired by http://errtheblog.com/posts/89-huba-huba
#
# This is idempotent, meaning you can run it over and over again without fear of
# breaking anything. Use it as an installer or to upgrade after merging from an
# upstream fork.

home = File.expand_path('~')
repo_root = File.expand_path(File.dirname(__FILE__))

# These directories contain host-local runtime state.  In particular, CC
# Switch and Codex mutate ~/.codex/config.toml, so linking the whole directory
# would make one machine overwrite another machine's paths and providers.
machine_local_dirs = %w[codex]

run_bootstrap = ARGV.delete('--bootstrap')
restore_agent_skills = !ARGV.delete('--skip-agent-skills')

def ensure_symlink(source, target)
  if File.symlink?(target)
    FileUtils.rm_f(target)
  elsif File.directory?(target)
    puts "[install] skip #{target}: exists and is not a symlink"
    return
  end

  FileUtils.ln_sf(source, target)
end

Dir.children(repo_root).each do |file|
  next if file.start_with?('.')
  next if file =~ /install/ || file =~ /README/ || file == 'config' || machine_local_dirs.include?(file)

  source = File.expand_path(file, repo_root)
  target = File.join(home, ".#{file}")
  ensure_symlink(source, target)
end

# Initialize only the portable Codex helpers inside a real, host-local
# ~/.codex directory.  Existing runtime config remains untouched because it
# is edited by Codex and CC Switch and may contain machine-specific paths.
codex_dir = File.join(home, '.codex')
if !File.symlink?(codex_dir)
  FileUtils.mkdir_p(codex_dir)

  common_source = File.join(repo_root, 'codex', 'config.common.toml')
  common_target = File.join(codex_dir, 'config.common.toml')
  ensure_symlink(common_source, common_target) if File.file?(common_source) && !File.exist?(common_target)

  index_source = File.join(repo_root, 'codex', 'update-project-index.py')
  index_target = File.join(codex_dir, 'update-project-index.py')
  ensure_symlink(index_source, index_target) if File.file?(index_source) && !File.exist?(index_target)

  projects_source = File.join(repo_root, 'codex', 'projects.local.toml.example')
  projects_target = File.join(codex_dir, 'projects.local.toml')
  if File.file?(projects_source) && !File.exist?(projects_target)
    FileUtils.cp(projects_source, projects_target)
    FileUtils.chmod(0o600, projects_target)
    puts "[install] created host-local #{projects_target}; review paths before use"
  end
else
  puts "[install] skip #{codex_dir}: existing symlink is host-managed"
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

agents_restore = File.join(repo_root, 'bin', 'agents-skills-restore')
if restore_agent_skills && File.executable?(agents_restore)
  puts "[install] restoring managed agent skills"
  unless system(agents_restore, '--adopt')
    warn '[install] managed agent skills restore failed; dotfiles initialization completed, retry after GitHub credentials are available'
  end
elsif !restore_agent_skills
  puts '[install] skipping managed agent skills (--skip-agent-skills)'
end
