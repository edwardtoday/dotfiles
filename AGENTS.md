# Repository Guidelines

## Project Structure & Module Organization
Root-level dotfiles mirror targets in your home directory. `install.rb` symlinks each item as `~/.<name>`. Place executable helpers in `bin/` (auto-sourced on PATH), platform bootstrap scripts under `init/`, app configs inside `config/`, and editor profiles in `vim/` and `emacs.d/`. Keep personal overrides in `~/.extra`; never commit secrets here.

## Build, Test, and Development Commands
- `./install.rb` – Pull latest changes, refresh symlinks, and source platform init scripts.
- `./osx` or `~/.osx` – Apply macOS defaults after install; rerun after major OS upgrades.
- `brew bundle ~/.Brewfile` – Install Homebrew formulae defined in `Brewfile`.
- `bash ./cask` – Install GUI apps listed in `cask` (idempotent).

## Coding Style & Naming Conventions
Favor POSIX-friendly Bash; start scripts with `#!/usr/bin/env bash` and two-space indentation. Keep line length ≤100 characters and prefer lowercase, hyphenated filenames (`shellaliases`, `gitconfig`). Use `shellcheck` before committing shell changes, `ruby -c install.rb` for Ruby syntax checks, and format Lua configs with `stylua` if available.

## Testing Guidelines
Run `shellcheck bin/*.sh` and `shellcheck init/**/*.sh` for lint coverage. Validate Ruby helpers with `bundle exec rubocop --lint` when the project Gemfile is present, otherwise `ruby -c`. After config edits, dry-run `./install.rb` and confirm symlinks via `ls -al ~ | grep dotfiles`.

## Commit & Pull Request Guidelines
Write concise commit messages in Chinese (e.g., “修复 zsh 启动脚本加载顺序”). Squash trivial fixups locally. Pull requests should state the motivation, summarize changed files, list validation steps (commands run), and include affected platform notes (macOS, Linux, WSL). Link related issues and attach screenshots or terminal snippets when the change alters prompts or visual output.

## Security & Configuration Tips
Store credentials in `~/.extra` or platform keychains; never add them to the repo. Review `git config --global --includes` after install to confirm expected overrides. For shared machines, audit `bin/` for executables that invoke privileged operations and document any required environment variables in `README.md`.
