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
```

Then run:

```bash
./github-agenda-sync doctor
./github-agenda-sync sync
```

The installer prepares a local `.env` file and shows the GitHub Actions secrets you need to create. It never prints secret values.

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
- Without a date, the issue is a Google Task.
- With a date and no times, it is an all-day Calendar event.
- Optional `calendar_start` and `calendar_end` use `HH:MM`.

## Required secrets

Configure these in GitHub Actions secrets:

- `GH_AGENDA_GITHUB_TOKEN`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REFRESH_TOKEN`

Optional repository variables:

- `GH_AGENDA_REPOSITORIES` — comma-separated `owner/repo` list
- `GOOGLE_TASKLIST_ID` — defaults to `@default`
- `GOOGLE_CALENDAR_ID` — defaults to `primary`
- `GOOGLE_TIMEZONE` — defaults to `UTC`

## Commands

```bash
./github-agenda-sync init
./github-agenda-sync doctor
./github-agenda-sync sync
./github-agenda-sync status
```

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

## Security

- No credentials are committed to the repository.
- `.env` is ignored.
- GitHub is the only source of truth.
- The project does not require your workstation to stay online when using GitHub Actions.

## License

MIT
