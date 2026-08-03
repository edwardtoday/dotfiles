# 开发工具环境重建

Time Machine 只保留源码、配置、项目锁文件和个人数据；可下载的软件本体、包管理器安装树、缓存及虚拟环境不进入备份。本页记录排除后的恢复顺序和实际清单位置。

## 1. 恢复 dotfiles

```bash
git clone https://github.com/edwardtoday/dotfiles.git ~/git/dotfiles
cd ~/git/dotfiles
./install.rb
```

私有凭据仍从单独保管的 `~/.extra_env`、钥匙串或密码管理器恢复，不应写入本仓库。

## 1.1 Agent skills

先确保 GitHub 对私有仓库 `edwardtoday/agent-skills-private` 的访问可用，再运行：

```bash
~/git/dotfiles/bin/agents-skills-restore --adopt
~/git/dotfiles/bin/agents-skills-audit
```

个人 skill 从私有仓恢复为 `~/.agents/skills` 下的软链接；第三方 skill 从 `agents/skills.yml` 指定的固定上游 revision 恢复。`~/.agents/.skill-lock.json` 是 `npx skills` 的安装器状态，不由 dotfiles 覆盖；其中的 Feishu/WeCom 记录保留给该安装器按需恢复。

## 2. Homebrew

安装 Homebrew 后执行：

```bash
brew bundle --file ~/git/dotfiles/Brewfile
```

`Brewfile` 记录当前机器的顶层 formula、cask、tap 和 Mac App Store 应用。Homebrew 会重新解析 formula 依赖，因此 `/opt/homebrew` 无需从 Time Machine 恢复。

## 3. Xcode 与 MacTeX

- Xcode：使用 Xcodes 或 Apple 官方渠道重新下载所需版本，再用 `sudo xcode-select --switch /Applications/Xcode-<版本>.app/Contents/Developer` 选择开发目录。
- Command Line Tools：完整 Xcode 未提供所需工具时运行 `xcode-select --install`。
- Xcode Server：当前目录是旧的软件安装树，没有需要恢复的用户项目；按需重新配置，不从备份还原。
- MacTeX：从官方安装包重新安装，TeX Live 会重建 `/usr/local/texlive`、`/Library/TeX` 和 `/Applications/TeX`。

项目的 `.xcodeproj`、`.xcworkspace`、Swift Package 锁文件、LaTeX 源文件和自定义模板仍应保留在源码仓库或 Time Machine 范围内。

## 4. Miniforge / Conda

先重新安装 arm64 Miniforge，然后恢复 base：

```bash
conda env update -n base -f ~/git/dotfiles/docs/rebuild/conda/exact/base.yml
```

再恢复项目环境：

```bash
for env in MinerU chattts ew2l faceswap; do
  conda env create -f "$HOME/git/dotfiles/docs/rebuild/conda/exact/$env.yml"
done
```

`exact/` 是当前环境的无 build 号快照，优先用于接近原样恢复；若旧版本已从 channel 下架，改用 `history/` 中的直接依赖清单创建环境，再由对应项目的锁文件或安装说明补齐 pip 依赖。

## 5. uv 工具与 Python

```bash
while IFS= read -r command; do
  [[ -z "$command" || "$command" == \#* ]] && continue
  eval "$command"
done < ~/git/dotfiles/docs/rebuild/uv-tools.txt
```

uv 管理的 Python 和工具环境位于 `~/.local/share/uv`，均可由 `docs/rebuild/uv-tools.txt` 重建。项目自身仍以 `pyproject.toml`、`uv.lock` 或 requirements 文件为准。

## 6. Go 与 Ruby 全局工具

```bash
while IFS= read -r command; do
  [[ -z "$command" || "$command" == \#* ]] && continue
  eval "$command"
done < ~/git/dotfiles/docs/rebuild/go-tools.txt

while IFS= read -r command; do
  [[ -z "$command" || "$command" == \#* ]] && continue
  eval "$command"
done < ~/git/dotfiles/docs/rebuild/ruby-tools.txt
```

`~/go/pkg` 只是 module/build cache；`~/.gem` 目前唯一需要主动保留的旧全局工具是 `video_transcoding`。项目依赖仍由各仓库的 `go.mod`、`Gemfile` 和锁文件恢复。

## 7. Time Machine 排除与回滚

预览、应用或撤销开发环境排除：

```bash
~/git/dotfiles/bin/tm-exclude-dev-artifacts --dry-run
sudo HOME="$HOME" ~/git/dotfiles/bin/tm-exclude-dev-artifacts --apply
sudo HOME="$HOME" ~/git/dotfiles/bin/tm-exclude-dev-artifacts --remove
```

排除不会删除本机文件，也不会影响当前程序运行；影响只发生在整机恢复时，届时按本页重新安装。应用缓存（企业微信 Chromium cache、Poe cache、Texpad bundle）会在应用再次运行时自动生成或下载。
