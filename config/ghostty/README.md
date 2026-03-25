# Ghostty

- 主配置文件：`config.ghostty`
- 安装后目标路径：`~/.config/ghostty/config.ghostty`
- 基于参考 gist 做了两处适配：
  - `background-blur-radius` 按 Ghostty 1.3.1 改为 `background-blur`
  - `theme` 改为真正的浅色/深色自动切换

如果本机没有安装 `Maple Mono NF CN`，Ghostty 会回退到 `MesloLGS NF`。

`global:ctrl+grave_accent=toggle_quick_terminal` 在 macOS 上需要给 Ghostty 授予“辅助功能”权限，否则全局快捷键不会生效。
