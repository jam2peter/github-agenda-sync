#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

printf '\nGitHub Agenda Sync installer\n\n'

command -v python3 >/dev/null || { echo 'ERROR: python3 is required.'; exit 1; }

if [ ! -f .env ]; then
  cp .env.example .env
  echo 'Created .env from template.'
else
  echo '.env already exists; keeping it.'
fi

chmod +x github-agenda-sync || true

echo
echo 'Next:'
echo '  1. Edit .env with your GitHub repositories and Google OAuth values.'
echo '  2. Run: ./github-agenda-sync doctor'
echo '  3. Run: ./github-agenda-sync sync'
echo
echo 'For GitHub Actions, copy .github/workflows/github-agenda-sync.yml into the repository where you want automation and configure the documented secrets/variables.'
