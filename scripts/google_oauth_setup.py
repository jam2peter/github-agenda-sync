#!/usr/bin/env python3
"""Interactive helper to obtain a Google OAuth refresh token for GitHub Agenda Sync."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/tasks",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a Google OAuth refresh token")
    parser.add_argument("client_json", help="Path to OAuth Desktop client JSON downloaded from Google Cloud")
    args = parser.parse_args()

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print("Missing dependency: google-auth-oauthlib", file=sys.stderr)
        print("Install it with: python3 -m pip install --user google-auth-oauthlib", file=sys.stderr)
        return 2

    client_path = pathlib.Path(args.client_json).expanduser().resolve()
    if not client_path.exists():
        print(f"Client JSON not found: {client_path}", file=sys.stderr)
        return 2

    flow = InstalledAppFlow.from_client_secrets_file(str(client_path), SCOPES)
    creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")

    data = json.loads(client_path.read_text())
    section = data.get("installed") or data.get("web") or {}

    print("\nGOOGLE_CLIENT_ID=")
    print(section.get("client_id", ""))
    print("\nGOOGLE_CLIENT_SECRET=")
    print(section.get("client_secret", ""))
    print("\nGOOGLE_REFRESH_TOKEN=")
    print(creds.refresh_token or "")
    print("\nStore these as GitHub Actions secrets. Do not commit them.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
