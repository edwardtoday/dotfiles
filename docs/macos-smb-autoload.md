# macOS SMB 自动挂载

`bin/m4mini-mount-smb-shares` 在用户登录后检查并挂载 mini 的四个常用共享：

- `proj` -> `/Volumes/proj`
- `yf1` -> `/Volumes/yf1`
- `上海` -> `/Volumes/did1000`
- `研究院` -> `/Volumes/LED_YJY`

它使用 `mount_smbfs -N`，只读取 macOS 登录钥匙串，不保存密码。LaunchAgent 在登录时运行，并每 120 秒补偿一次网络尚未恢复的情况。已挂载的共享会跳过，不会重复挂载。

日志位于 `~/Library/Logs/io.qingpei.smb-mounts.log`。移除 `~/Library/LaunchAgents/io.qingpei.smb-mounts.plist` 并卸载对应共享即可回滚。
