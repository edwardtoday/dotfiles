#!/usr/bin/env python3
"""Codex agent notification hook for macOS via terminal-notifier."""

import json
import subprocess
import sys
from typing import Any


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


def main(argv: list[str]) -> int:
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

    command.extend(["-ignoreDnD", "-activate", "com.googlecode.iterm2"])

    # 使用终端通知器发送系统通知
    subprocess.run(command, check=False)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
