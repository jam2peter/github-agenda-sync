# Installation

## Local installation

```bash
git clone https://github.com/jam2peter/github-agenda-sync.git
cd github-agenda-sync
chmod +x install.sh github-agenda-sync
./install.sh
```

Edit `.env`, then run:

```bash
./github-agenda-sync doctor
./github-agenda-sync sync
```

## GitHub Actions

Configure these repository secrets:

- `GH_AGENDA_GITHUB_TOKEN`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REFRESH_TOKEN`

Configure at least this repository variable:

- `GH_AGENDA_REPOSITORIES=owner/repository`

Optional variables:

- `GOOGLE_TASKLIST_ID=@default`
- `GOOGLE_CALENDAR_ID=primary`
- `GOOGLE_TIMEZONE=UTC`
- `GOOGLE_EVENT_DEFAULT_MINUTES=60`

The included workflow runs on issue changes, manually, and twice per hour.

## Add an issue to the sync

Put this in the issue body:

```text
<!-- GH_AGENDA_SYNC
managed=true
start_date=
target_date=
calendar_start=
calendar_end=
-->
```

With no date, the issue becomes a Google Task. Add a date and it becomes a Calendar event.
