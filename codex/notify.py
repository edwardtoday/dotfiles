#!/usr/bin/env python3
"""Codex agent notification hook for macOS via terminal-notifier."""

import json
import os
import shlex
import subprocess
import sys
from typing import Any

DEFAULT_ACTIVATE_BUNDLE_ID = "com.mitchellh.ghostty"
FOCUS_LOG_PATH = os.path.expanduser("~/.codex/notify-focus.log")

FOCUS_GHOSTTY_SCRIPT = """
on run argv
    set targetDir to item 1 of argv
    tell application "Ghostty"
        activate
        repeat with ghosttyWindow in windows
            repeat with ghosttyTab in tabs of ghosttyWindow
                repeat with ghosttyTerminal in terminals of ghosttyTab
                    try
                        if working directory of ghosttyTerminal is targetDir then
                            select tab ghosttyTab
                            activate window ghosttyWindow
                            focus ghosttyTerminal
                            return
                        end if
                    end try
                end repeat
            end repeat
        end repeat
    end tell
end run
"""


def load_notification(raw: str) -> dict[str, Any]:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def build_payload(notification: dict[str, Any]) -> tuple[str, str, str]:
    notification_type = notification.get("type")
    if notification_type != "agent-turn-complete":
        return "", "", ""

    assistant_message = notification.get("last-assistant-message") or "Codex: Turn Complete!"
    input_messages = notification.get("input-messages") or []
    message = " ".join(str(part) for part in input_messages if part)

    title = assistant_message
    if not title.lower().startswith("codex"):
        title = f"Codex: {title}"

    group = "codex-" + str(notification.get("thread-id", ""))

    return title, message or "任务已完成。", group


def focus_ghostty(cwd: str) -> int:
    with open(FOCUS_LOG_PATH, "a", encoding="utf-8") as log:
        log.write(f"focus requested cwd={cwd!r}\n")
    result = subprocess.run(
        ["osascript", "-e", FOCUS_GHOSTTY_SCRIPT, cwd],
        capture_output=True,
        text=True,
        check=False,
    )
    with open(FOCUS_LOG_PATH, "a", encoding="utf-8") as log:
        if result.stdout:
            log.write(f"osascript stdout={result.stdout!r}\n")
        if result.stderr:
            log.write(f"osascript stderr={result.stderr!r}\n")
        log.write(f"osascript rc={result.returncode}\n")
    if result.returncode != 0:
        subprocess.run(["open", "-b", DEFAULT_ACTIVATE_BUNDLE_ID], check=False)
    return result.returncode


def main(argv: list[str]) -> int:
    if len(argv) == 3 and argv[1] == "--focus-ghostty":
        return focus_ghostty(argv[2])

    if len(argv) != 2:
        print("Usage: notify.py <NOTIFICATION_JSON>")
        return 1

    notification = load_notification(argv[1])
    if not notification:
        return 1

    title, message, group = build_payload(notification)
    if not title:
        return 0

    command = [
        "terminal-notifier",
        "-title",
        title,
        "-message",
        message,
    ]

    if group:
        command.extend(["-group", group])

    command.extend(["-ignoreDnD"])

    cwd = str(notification.get("cwd") or os.getcwd())
    focus_command = " ".join(
        shlex.quote(part)
        for part in [sys.executable, os.path.abspath(__file__), "--focus-ghostty", cwd]
    )
    command.extend(["-execute", focus_command])

    # 使用终端通知器发送系统通知
    subprocess.run(command, check=False)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
