# Clash TUN Watchdog

`clash-tun-watchdog` captures local network evidence before recovering from a
stale Clash Verge/Mihomo TUN path. It uses the local Mihomo Unix socket and does
not require internet access to capture the route, DNS, interface, and runtime
TUN state.

## Policy

- The LaunchAgent runs once per minute.
- A normal tick only computes a local network fingerprint.
- Connectivity probes run after a network fingerprint change, every 3 minutes
  on AC power, every 5 minutes on battery, while confirming a failure, or while
  the watchdog owns a fail-open state.
- Three consecutive public-connectivity failures, or three consecutive GitLab
  certificate-validation failures, trigger fail-open. After the first failure,
  the remaining confirmations run five seconds apart in the same tick.
- Evidence is written under `/tmp/clash-tun-watchdog-<uid>/events/` before the
  TUN setting changes.
- The watchdog only re-enables a TUN that it disabled itself. A user-disabled
  TUN is left alone.
- In fail-open state, a healthy direct probe triggers an enable attempt. A
  failed attempt returns to fail-open and retries with bounded backoff.
- All state and evidence is under `/tmp`. The first tick after a reboot also
  compares the boot identifier and removes evidence from the previous boot.

The evidence excludes subscriptions, API tokens, request bodies, raw packets,
and the complete connection list. It includes public TLS leaf metadata because
certificate drift is one of the target failure signals.

## Commands

```bash
clash-tun-watchdog status
clash-tun-watchdog capture
clash-tun-watchdog run --force-probe --dry-run
```

`capture` is read-only and can be run immediately before manually toggling TUN.

## Install

```bash
ln -s /Users/qingpei/git/dotfiles/launchd/com.edwardtoday.clash-tun-watchdog.plist \
  "$HOME/Library/LaunchAgents/com.edwardtoday.clash-tun-watchdog.plist"
launchctl bootstrap "gui/$(id -u)" \
  "$HOME/Library/LaunchAgents/com.edwardtoday.clash-tun-watchdog.plist"
```

## Roll Back

```bash
launchctl bootout "gui/$(id -u)/com.edwardtoday.clash-tun-watchdog"
rm "$HOME/Library/LaunchAgents/com.edwardtoday.clash-tun-watchdog.plist"
```

The rollback does not modify Clash Verge profiles. If the watchdog currently
owns fail-open, manually enable TUN in Clash Verge after unloading it.
