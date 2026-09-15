#!/usr/bin/env bash
set -euo pipefail

if ! command -v gh >/dev/null 2>&1; then
  echo "ERROR: GitHub CLI (gh) is required." >&2
  exit 2
fi
if ! gh auth status >/dev/null 2>&1; then
  echo "ERROR: authenticate first with: gh auth login" >&2
  exit 2
fi

REPO="${1:-}"
if [ -z "$REPO" ]; then
  REPO="$(gh repo view --json nameWithOwner --jq .nameWithOwner 2>/dev/null || true)"
fi
[ -n "$REPO" ] || { echo "Usage: $0 owner/repository" >&2; exit 2; }

GH_AGENDA_REPOSITORIES="${GH_AGENDA_REPOSITORIES:-}"
GOOGLE_TIMEZONE="${GOOGLE_TIMEZONE:-}"
GOOGLE_CALENDAR_ID="${GOOGLE_CALENDAR_ID:-}"
GOOGLE_TASKLIST_ID="${GOOGLE_TASKLIST_ID:-}"

if [ -z "$GH_AGENDA_REPOSITORIES" ]; then read -r -p "Repositories to sync (comma-separated owner/repo): " GH_AGENDA_REPOSITORIES; fi
if [ -z "$GOOGLE_TIMEZONE" ]; then read -r -p "Google timezone [UTC]: " GOOGLE_TIMEZONE; fi
GOOGLE_TIMEZONE="${GOOGLE_TIMEZONE:-UTC}"
if [ -z "$GOOGLE_CALENDAR_ID" ]; then read -r -p "Google Calendar ID [primary]: " GOOGLE_CALENDAR_ID; fi
GOOGLE_CALENDAR_ID="${GOOGLE_CALENDAR_ID:-primary}"
if [ -z "$GOOGLE_TASKLIST_ID" ]; then read -r -p "Google Tasklist ID [@default]: " GOOGLE_TASKLIST_ID; fi
GOOGLE_TASKLIST_ID="${GOOGLE_TASKLIST_ID:-@default}"

if [ -z "${GH_AGENDA_GITHUB_TOKEN:-}" ]; then echo; read -r -s -p "GitHub token with access to Issues: " GH_AGENDA_GITHUB_TOKEN; echo; fi
if [ -z "${GOOGLE_CLIENT_ID:-}" ]; then read -r -s -p "Google Client ID: " GOOGLE_CLIENT_ID; echo; fi
if [ -z "${GOOGLE_CLIENT_SECRET:-}" ]; then read -r -s -p "Google Client Secret: " GOOGLE_CLIENT_SECRET; echo; fi
if [ -z "${GOOGLE_REFRESH_TOKEN:-}" ]; then read -r -s -p "Google Refresh Token: " GOOGLE_REFRESH_TOKEN; echo; fi

for name in GH_AGENDA_REPOSITORIES GH_AGENDA_GITHUB_TOKEN GOOGLE_CLIENT_ID GOOGLE_CLIENT_SECRET GOOGLE_REFRESH_TOKEN; do
  [ -n "${!name:-}" ] || { echo "ERROR: $name is required." >&2; exit 2; }
done

printf '%s' "$GH_AGENDA_GITHUB_TOKEN" | gh secret set GH_AGENDA_GITHUB_TOKEN --repo "$REPO"
printf '%s' "$GOOGLE_CLIENT_ID" | gh secret set GOOGLE_CLIENT_ID --repo "$REPO"
printf '%s' "$GOOGLE_CLIENT_SECRET" | gh secret set GOOGLE_CLIENT_SECRET --repo "$REPO"
printf '%s' "$GOOGLE_REFRESH_TOKEN" | gh secret set GOOGLE_REFRESH_TOKEN --repo "$REPO"
gh variable set GH_AGENDA_REPOSITORIES --body "$GH_AGENDA_REPOSITORIES" --repo "$REPO"
gh variable set GOOGLE_TIMEZONE --body "$GOOGLE_TIMEZONE" --repo "$REPO"
gh variable set GOOGLE_CALENDAR_ID --body "$GOOGLE_CALENDAR_ID" --repo "$REPO"
gh variable set GOOGLE_TASKLIST_ID --body "$GOOGLE_TASKLIST_ID" --repo "$REPO"

echo "GITHUB_ACTIONS_CONFIGURATION=SUCCESS"
echo "REPOSITORY=$REPO"
