#!/usr/bin/env python3
"""Interactive helper to obtain Google OAuth credentials for GitHub Agenda Sync."""

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
    parser = argparse.ArgumentParser(description="Generate Google OAuth credentials")
    parser.add_argument("client_json", help="OAuth Desktop client JSON downloaded from Google Cloud")
    parser.add_argument("--env-file", help="Write credentials to a private shell env file instead of stdout")
    args = parser.parse_args()

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print("Missing dependency: google-auth-oauthlib", file=sys.stderr)
        print("Install it inside a virtual environment with: pip install google-auth-oauthlib", file=sys.stderr)
        return 2

    client_path = pathlib.Path(args.client_json).expanduser().resolve()
    if not client_path.exists():
        print(f"Client JSON not found: {client_path}", file=sys.stderr)
        return 2

    flow = InstalledAppFlow.from_client_secrets_file(str(client_path), SCOPES)
    creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")

    data = json.loads(client_path.read_text())
    section = data.get("installed") or data.get("web") or {}
    values = {
        "GOOGLE_CLIENT_ID": section.get("client_id", ""),
        "GOOGLE_CLIENT_SECRET": section.get("client_secret", ""),
        "GOOGLE_REFRESH_TOKEN": creds.refresh_token or "",
    }
    if not all(values.values()):
        print("ERROR: OAuth flow did not return all required credentials.", file=sys.stderr)
        return 3

    if args.env_file:
        out = pathlib.Path(args.env_file).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("".join(f"{key}={json.dumps(value)}\n" for key, value in values.items()))
        out.chmod(0o600)
        print(f"OAUTH_RESULT=SUCCESS\nCREDENTIAL_FILE={out}\nFILE_MODE=600")
    else:
        for key, value in values.items():
            print(f"{key}={value}")
        print("Store these as GitHub Actions secrets. Do not commit them.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
