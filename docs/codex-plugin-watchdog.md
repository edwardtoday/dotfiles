# Codex 内置插件路径看护

LaunchAgent `com.edwardtoday.codex-plugin-watchdog` 登录时启动，每 30 秒检查一次。
脚本只把已确认故障的解析后真实路径改回 `~/.codex/.tmp/bundled-marketplaces/openai-bundled` 的绝对逻辑路径。
其他路径、缺失字段、无效 TOML、缺失插件目录均不自动重建。保留其他配置和注释，不启用被手工禁用的插件。

日志：`~/Library/Logs/codex-plugin-watchdog/events.log`；最近检查：同目录 `status.json`。
日志只包含状态、时间和修复后哈希，不保存配置或凭据。事件日志超过 1MB 时保留上一份。

写入使用同目录临时文件和原子替换，保留文件权限；写前重读检测并发变化。
这不是与 App 共享的事务锁，最终检查和替换之间仍存在极短的竞争窗口。
看护只修配置，不重启 App、不控制前台。App 缓存未刷新时仍可能需要刷新插件页或重开 App。

停用：`launchctl bootout gui/$(id -u)/com.edwardtoday.codex-plugin-watchdog`。
取消下次登录加载：移除 `~/Library/LaunchAgents/com.edwardtoday.codex-plugin-watchdog.plist` 链接。
脚本、日志和其他配置可保留。该看护不是任意 Computer Use 故障的通用修复器。
