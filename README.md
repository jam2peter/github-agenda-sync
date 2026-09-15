# GitHub Agenda Sync

Synchronize GitHub Issues one-way to Google Tasks and Google Calendar.

- Open issue without a date -> Google Task
- Open issue with a date -> Google Calendar event
- Add a date -> Task becomes Event
- Remove the date -> Event becomes Task
- Close the issue -> Task is completed / Event is removed
- GitHub remains the source of truth
- Reconciliation is idempotent: unchanged items are not rewritten

## Quick start

```bash
git clone https://github.com/jam2peter/github-agenda-sync.git
cd github-agenda-sync
./install.sh
./github-agenda-sync setup
```

The guided setup:

1. checks Python and GitHub CLI (`gh`)
2. authenticates GitHub when needed
3. detects the current repository
4. asks which repositories should be synchronized
5. asks for timezone, Calendar ID and Tasklist ID
6. opens Google OAuth authorization from a Desktop OAuth client JSON
7. stores Google/GitHub credentials as GitHub Actions secrets
8. stores non-secret settings as GitHub Actions variables
9. creates a local `.env` containing only non-secret settings

After setup:

```bash
./github-agenda-sync doctor
gh workflow run github-agenda-sync.yml --repo OWNER/REPOSITORY
```

## Google prerequisite

Create a Google Cloud OAuth **Desktop app**, enable Google Calendar API and Google Tasks API, and download the client JSON file. During `setup`, provide the path to that file.

Required OAuth scopes:

- `https://www.googleapis.com/auth/calendar.events`
- `https://www.googleapis.com/auth/tasks`

See `docs/GOOGLE-OAUTH.md` for details.

## Managed issue metadata

Add this block to an issue body:

```text
<!-- GH_AGENDA_SYNC
managed=true
start_date=2026-09-20
target_date=
calendar_start=09:00
calendar_end=10:00
-->
```

Rules:

- `managed=true` enables synchronization for the issue.
- `start_date` or `target_date` may contain `YYYY-MM-DD`.
- `start_date` takes precedence over `target_date`.
- Without a date, the issue is a Google Task.
- With a date and no times, it is an all-day Calendar event.
- Optional `calendar_start` and `calendar_end` use `HH:MM`.

## GitHub Actions configuration

The setup command configures these secrets automatically:

- `GH_AGENDA_GITHUB_TOKEN`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REFRESH_TOKEN`

And these variables:

- `GH_AGENDA_REPOSITORIES`
- `GOOGLE_TASKLIST_ID`
- `GOOGLE_CALENDAR_ID`
- `GOOGLE_TIMEZONE`

The included workflow runs on issue changes, manual dispatch, and a twice-hourly schedule.

## Commands

```bash
./github-agenda-sync setup [owner/repository]
./github-agenda-sync doctor
./github-agenda-sync sync
./github-agenda-sync status
```

Local `sync` is intended mainly for development. The recommended always-on mode is GitHub Actions.

## Architecture

```text
GitHub Issues
     |
     v
GitHub Agenda Sync
     |
     +--> no date --> Google Tasks
     |
     +--> dated ----> Google Calendar
```

Google never writes back to GitHub.

## Tests

The repository includes unit tests for metadata parsing, date selection, all-day event generation and idempotent Calendar normalization.

Run locally with:

```bash
python3 -m unittest discover -s tests -v
```

They also run automatically in GitHub Actions.

## Security

- No credentials are committed to the repository.
- OAuth credentials are passed through a temporary file with mode `600` during guided setup.
- The local `.env` contains only non-secret configuration after guided setup.
- Google client secret and refresh token are stored as GitHub Actions secrets.
- The project is one-way: Google cannot modify GitHub Issues.
- The workstation does not need to remain online when using GitHub Actions.
- Do not commit downloaded Google OAuth client JSON files.

## Current release status

The project is currently an early public MVP. Before a stable `v1.0`, perform a clean-room installation with a separate test repository/account configuration and verify the full Task -> Event -> Task -> closed lifecycle.

## License

MIT
