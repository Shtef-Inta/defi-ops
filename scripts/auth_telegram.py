#!/usr/bin/env python3
"""Non-interactive Telegram auth for Telethon user session."""
import argparse
import json
import os
import sys
from pathlib import Path

from telethon.sync import TelegramClient  # type: ignore[import-untyped]

STATE_DIR = Path(__file__).parent.parent / "state"
SESSION_PATH = STATE_DIR / "telegram.session"
AUTH_STATE_PATH = STATE_DIR / "telegram_auth_state.json"

API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]


def cmd_send_code(phone: str) -> None:
    client = TelegramClient(str(SESSION_PATH), API_ID, API_HASH)
    client.connect()
    if client.is_user_authorized():
        print("Already authorized.")
        client.disconnect()
        sys.exit(0)
    result = client.send_code_request(phone)
    AUTH_STATE_PATH.write_text(json.dumps({
        "phone": phone,
        "phone_code_hash": result.phone_code_hash,
    }))
    print(f"Code sent to {phone}. Check Telegram and run sign-in with the code.")
    client.disconnect()


def cmd_sign_in(phone: str, code: str) -> None:
    state = json.loads(AUTH_STATE_PATH.read_text())
    if state["phone"] != phone:
        print("Phone mismatch.")
        sys.exit(1)
    client = TelegramClient(str(SESSION_PATH), API_ID, API_HASH)
    client.connect()
    try:
        client.sign_in(phone, code, phone_code_hash=state["phone_code_hash"])
    except Exception as exc:
        print(f"Sign-in failed: {exc}")
        sys.exit(1)
    print("Authorized successfully.")
    client.disconnect()
    AUTH_STATE_PATH.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")

    p1 = sub.add_parser("send-code")
    p1.add_argument("phone")

    p2 = sub.add_parser("sign-in")
    p2.add_argument("phone")
    p2.add_argument("code")

    args = parser.parse_args()
    if args.cmd == "send-code":
        cmd_send_code(args.phone)
    elif args.cmd == "sign-in":
        cmd_sign_in(args.phone, args.code)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
