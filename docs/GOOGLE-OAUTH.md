# Google OAuth setup

GitHub Agenda Sync needs OAuth access to Google Tasks and Google Calendar.

## Google Cloud

1. Create or choose a Google Cloud project.
2. Enable **Google Calendar API** and **Google Tasks API**.
3. Configure the OAuth consent screen.
4. Create an OAuth Client of type **Desktop app**.
5. Grant these scopes:
   - `https://www.googleapis.com/auth/calendar.events`
   - `https://www.googleapis.com/auth/tasks`
6. Generate a refresh token for the same OAuth client.

Keep the following values private:

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REFRESH_TOKEN`

For local use, place them only in `.env`.
For GitHub Actions, store them only as repository Actions secrets.

Never commit credentials, OAuth JSON files, access tokens, or refresh tokens.
