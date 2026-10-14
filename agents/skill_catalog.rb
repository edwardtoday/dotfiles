# frozen_string_literal: true

require 'digest'
require 'fileutils'
require 'find'
require 'json'
require 'pathname'
require 'rubygems/package'
require 'tmpdir'
require 'zlib'

module SkillCatalog
  EXCLUDED = %w[.git .DS_Store __pycache__ node_modules .playwright-cli].freeze

  def self.expand(path)
    File.expand_path(path.sub(/\A~/, Dir.home))
  end

  def self.entries(directory)
    root = File.realpath(directory)
    entries = []
    Find.find(root) do |path|
      next if path == root
      relative = path.delete_prefix("#{root}/")
      if EXCLUDED.include?(File.basename(path)) || path.end_with?('.pyc')
        File.directory?(path) ? Find.prune : next
      end
      raise "nested symlink requires separate review: #{relative}" if File.symlink?(path)
      next if File.directory?(path)
      raise "unsupported file type: #{relative}" unless File.file?(path)
      entries << [relative, File.stat(path).mode & 0o777, Digest::SHA256.file(path).hexdigest]
    end
    entries.sort_by(&:first)
  end

  def self.fingerprint(directory)
    Digest::SHA256.hexdigest(JSON.generate(entries(directory)))
  end

  def self.snapshot(directory, destination)
    rows = entries(directory)
    fingerprint = Digest::SHA256.hexdigest(JSON.generate(rows))
    FileUtils.mkdir_p(destination, mode: 0o700)
    archive = File.join(destination, "#{fingerprint}.tar.gz")
    unless File.exist?(archive)
      temporary = "#{archive}.#{Process.pid}.tmp"
      begin
        File.open(temporary, File::WRONLY | File::CREAT | File::EXCL, 0o600) do |file|
          gzip = Zlib::GzipWriter.new(file)
          Gem::Package::TarWriter.new(gzip) do |tar|
            rows.each do |relative, mode, _|
              source = File.join(directory, relative)
              tar.add_file_simple(relative, mode, File.size(source)) { |entry| entry.write(File.binread(source)) }
            end
          end
          gzip.close
        end
        raise 'skill changed while snapshotting' unless fingerprint(directory) == fingerprint
        File.rename(temporary, archive)
      ensure
        File.unlink(temporary) if File.exist?(temporary)
      end
    end
    { 'tree_sha256' => fingerprint, 'archive' => archive, 'archive_sha256' => Digest::SHA256.file(archive).hexdigest }
  end

  def self.restore(record, materialized_root)
    target = expand(record.fetch('runtime_path'))
    raise "refusing to replace existing skill: #{target}" if File.exist?(target) || File.symlink?(target)
    archive = expand(record.fetch('archive'))
    raise 'snapshot checksum mismatch' unless Digest::SHA256.file(archive).hexdigest == record.fetch('archive_sha256')
    digest = record.fetch('tree_sha256')
    raise 'invalid content digest' unless digest.match?(/\A[0-9a-f]{64}\z/)
    FileUtils.mkdir_p(materialized_root, mode: 0o700)
    final = File.join(materialized_root, digest)
    temporary = nil
    begin
      unless File.exist?(final)
        temporary = Dir.mktmpdir('.skill-restore-', materialized_root)
        Zlib::GzipReader.open(archive) do |gzip|
          Gem::Package::TarReader.new(gzip) do |tar|
            tar.each do |entry|
              relative = entry.full_name
              # 快照只接受相对普通文件，避免路径穿越和符号链接逃逸。
              components = relative.split('/')
              raise 'unsafe snapshot path' if relative.start_with?('/') || components.any? { |p| p.empty? || p == '..' || p == '.' }
              raise 'unsupported snapshot entry' unless entry.file?
              path = File.join(temporary, relative)
              FileUtils.mkdir_p(File.dirname(path))
              File.open(path, File::WRONLY | File::CREAT | File::EXCL, entry.header.mode & 0o777) { |f| IO.copy_stream(entry, f) }
            end
          end
        end
        raise 'restored skill fingerprint mismatch' unless fingerprint(temporary) == digest
        File.rename(temporary, final)
        temporary = nil
      end
      raise 'materialized snapshot fingerprint mismatch' unless fingerprint(final) == digest
      FileUtils.mkdir_p(File.dirname(target))
      File.symlink(final, target)
    ensure
      FileUtils.remove_entry(temporary) if temporary && File.exist?(temporary)
    end
    target
  end
end
