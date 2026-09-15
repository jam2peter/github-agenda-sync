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
if [ -z "$REPO" ]; then
  echo "Usage: $0 owner/repository" >&2
  exit 2
fi

read -r -p "Repositories to sync (comma-separated owner/repo): " SYNC_REPOSITORIES
read -r -p "Google timezone [America/Sao_Paulo]: " GOOGLE_TIMEZONE
GOOGLE_TIMEZONE="${GOOGLE_TIMEZONE:-America/Sao_Paulo}"
read -r -p "Google Calendar ID [primary]: " GOOGLE_CALENDAR_ID
GOOGLE_CALENDAR_ID="${GOOGLE_CALENDAR_ID:-primary}"
read -r -p "Google Tasklist ID [@default]: " GOOGLE_TASKLIST_ID
GOOGLE_TASKLIST_ID="${GOOGLE_TASKLIST_ID:-@default}"

echo
read -r -s -p "GitHub token with access to Issues: " PROJECTS_TOKEN
echo
read -r -s -p "Google Client ID: " GOOGLE_CLIENT_ID
echo
read -r -s -p "Google Client Secret: " GOOGLE_CLIENT_SECRET
echo
read -r -s -p "Google Refresh Token: " GOOGLE_REFRESH_TOKEN
echo

printf '%s' "$PROJECTS_TOKEN" | gh secret set PROJECTS_TOKEN --repo "$REPO"
printf '%s' "$GOOGLE_CLIENT_ID" | gh secret set GOOGLE_CLIENT_ID --repo "$REPO"
printf '%s' "$GOOGLE_CLIENT_SECRET" | gh secret set GOOGLE_CLIENT_SECRET --repo "$REPO"
printf '%s' "$GOOGLE_REFRESH_TOKEN" | gh secret set GOOGLE_REFRESH_TOKEN --repo "$REPO"

gh variable set SYNC_REPOSITORIES --body "$SYNC_REPOSITORIES" --repo "$REPO"
gh variable set GOOGLE_TIMEZONE --body "$GOOGLE_TIMEZONE" --repo "$REPO"
gh variable set GOOGLE_CALENDAR_ID --body "$GOOGLE_CALENDAR_ID" --repo "$REPO"
gh variable set GOOGLE_TASKLIST_ID --body "$GOOGLE_TASKLIST_ID" --repo "$REPO"

echo
echo "GitHub Actions configuration complete for $REPO"
echo "Run: gh workflow run github-agenda-sync.yml --repo $REPO"
