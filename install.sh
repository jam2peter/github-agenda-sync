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

chmod +x github-agenda-sync scripts/configure_github.sh || true

echo
echo 'Installation ready.'
echo
echo 'Recommended next step:'
echo '  ./github-agenda-sync setup'
echo
echo 'Then:'
echo '  ./github-agenda-sync doctor'
echo '  ./github-agenda-sync sync'
echo
echo 'For automatic operation, the setup command configures GitHub Actions secrets and variables.'
