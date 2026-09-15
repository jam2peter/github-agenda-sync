#!/usr/bin/env python3
"""One-way sync: GitHub Issues -> Google Tasks / Google Calendar."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

GH_TOKEN = os.environ.get("GH_AGENDA_GITHUB_TOKEN", "")
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REFRESH_TOKEN = os.environ.get("GOOGLE_REFRESH_TOKEN", "")
TASKLIST_ID = os.environ.get("GOOGLE_TASKLIST_ID", "@default")
CALENDAR_ID = os.environ.get("GOOGLE_CALENDAR_ID", "primary")
TIMEZONE = os.environ.get("GOOGLE_TIMEZONE", "UTC")
DEFAULT_MINUTES = int(os.environ.get("GOOGLE_EVENT_DEFAULT_MINUTES", "60"))
REPOSITORIES = [x.strip() for x in os.environ.get("GH_AGENDA_REPOSITORIES", "").split(",") if x.strip()]

META_RE = re.compile(r"<!--\s*GH_AGENDA_SYNC\s*(.*?)-->", re.S | re.I)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TIME_RE = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")


def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(1)


def request_json(url: str, *, method: str = "GET", payload: dict | None = None, headers: dict[str, str] | None = None) -> object:
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("User-Agent", "github-agenda-sync/0.1")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        die(f"HTTP {exc.code}: {body[:500]}")


def google_access_token() -> str:
    missing = [k for k, v in (("GOOGLE_CLIENT_ID", GOOGLE_CLIENT_ID), ("GOOGLE_CLIENT_SECRET", GOOGLE_CLIENT_SECRET), ("GOOGLE_REFRESH_TOKEN", GOOGLE_REFRESH_TOKEN)) if not v]
    if missing:
        die("missing Google OAuth values: " + ", ".join(missing))
    form = urllib.parse.urlencode({
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "refresh_token": GOOGLE_REFRESH_TOKEN,
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=form, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())["access_token"]


def gh_get(url: str) -> object:
    if not GH_TOKEN:
        die("GH_AGENDA_GITHUB_TOKEN is not configured")
    return request_json(url, headers={"Authorization": f"Bearer {GH_TOKEN}", "Accept": "application/vnd.github+json"})


def parse_metadata(body: str | None) -> dict[str, str] | None:
    m = META_RE.search(body or "")
    if not m:
        return None
    out = {}
    for raw in m.group(1).splitlines():
        raw = raw.strip()
        if raw and "=" in raw and not raw.startswith("#"):
            k, v = raw.split("=", 1)
            out[k.strip().lower()] = v.strip()
    return out


def managed(meta: dict[str, str] | None) -> bool:
    if not meta:
        return False
    return meta.get("managed", "true").lower() in {"1", "true", "yes", "on"}


def chosen_date(meta: dict[str, str]) -> str | None:
    for key in ("start_date", "target_date"):
        value = meta.get(key, "")
        if value and DATE_RE.fullmatch(value):
            return value
    return None


def list_issues(repo: str) -> list[dict]:
    if "/" not in repo:
        die(f"invalid repository: {repo}")
    owner, name = repo.split("/", 1)
    out = []
    page = 1
    while True:
        url = f"https://api.github.com/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(name)}/issues?state=all&per_page=100&page={page}"
        batch = gh_get(url)
        assert isinstance(batch, list)
        for issue in batch:
            if "pull_request" not in issue:
                issue["_repo"] = repo
                out.append(issue)
        if len(batch) < 100:
            break
        page += 1
    return out


def key_for(issue: dict) -> str:
    return f"github:{issue['_repo']}#{issue['number']}"


def issue_url(issue: dict) -> str:
    return issue.get("html_url") or f"https://github.com/{issue['_repo']}/issues/{issue['number']}"


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def marker(key: str) -> str:
    return f"[GH_AGENDA_SYNC:{key}]"


def list_tasks(token: str) -> list[dict]:
    url = f"https://tasks.googleapis.com/tasks/v1/lists/{urllib.parse.quote(TASKLIST_ID, safe='@')}/tasks?showCompleted=true&showHidden=true&maxResults=100"
    data = request_json(url, headers=auth(token))
    assert isinstance(data, dict)
    return data.get("items", [])


def find_task(tasks: list[dict], key: str) -> dict | None:
    m = marker(key)
    return next((t for t in tasks if m in (t.get("notes") or "")), None)


def task_payload(issue: dict, key: str) -> dict:
    return {"title": issue["title"], "notes": f"{marker(key)}\nSource: {issue_url(issue)}\nOne-way sync: GitHub -> Google.", "status": "needsAction"}


def upsert_task(token: str, tasks: list[dict], issue: dict, key: str) -> bool:
    payload = task_payload(issue, key)
    found = find_task(tasks, key)
    base = f"https://tasks.googleapis.com/tasks/v1/lists/{urllib.parse.quote(TASKLIST_ID, safe='@')}/tasks"
    if found:
        current = {k: found.get(k, "" if k != "status" else "needsAction") for k in ("title", "notes", "status")}
        if current == payload:
            print(f"TASK NO_CHANGE {key}")
            return False
        request_json(f"{base}/{urllib.parse.quote(found['id'])}", method="PATCH", payload=payload, headers=auth(token))
        print(f"TASK UPDATE {key}")
        return True
    request_json(base, method="POST", payload=payload, headers=auth(token))
    print(f"TASK CREATE {key}")
    return True


def complete_task(token: str, task: dict) -> None:
    url = f"https://tasks.googleapis.com/tasks/v1/lists/{urllib.parse.quote(TASKLIST_ID, safe='@')}/tasks/{urllib.parse.quote(task['id'])}"
    request_json(url, method="PATCH", payload={"status": "completed"}, headers=auth(token))


def delete_task(token: str, task: dict) -> None:
    url = f"https://tasks.googleapis.com/tasks/v1/lists/{urllib.parse.quote(TASKLIST_ID, safe='@')}/tasks/{urllib.parse.quote(task['id'])}"
    request_json(url, method="DELETE", headers=auth(token))


def find_event(token: str, key: str) -> dict | None:
    params = urllib.parse.urlencode({"privateExtendedProperty": f"gh_agenda_issue={key}", "showDeleted": "true", "maxResults": "10"})
    url = f"https://www.googleapis.com/calendar/v3/calendars/{urllib.parse.quote(CALENDAR_ID, safe='@')}/events?{params}"
    data = request_json(url, headers=auth(token))
    assert isinstance(data, dict)
    items = data.get("items", [])
    return items[0] if items else None


def event_payload(issue: dict, meta: dict[str, str], key: str, date: str) -> dict:
    payload = {
        "summary": issue["title"],
        "description": f"GitHub source: {issue_url(issue)}\nOne-way sync: GitHub -> Google.",
        "extendedProperties": {"private": {"gh_agenda_issue": key}},
        "reminders": {"useDefault": False, "overrides": [{"method": "popup", "minutes": 30}, {"method": "popup", "minutes": 5}]},
    }
    start, end = meta.get("calendar_start", ""), meta.get("calendar_end", "")
    if start or end:
        if start and not TIME_RE.fullmatch(start):
            die(f"invalid calendar_start for {key}: {start}")
        if end and not TIME_RE.fullmatch(end):
            die(f"invalid calendar_end for {key}: {end}")
        start = start or "09:00"
        if not end:
            hh, mm = map(int, start.split(":"))
            total = hh * 60 + mm + DEFAULT_MINUTES
            end = f"{(total // 60) % 24:02d}:{total % 60:02d}"
        payload["start"] = {"dateTime": f"{date}T{start}:00", "timeZone": TIMEZONE}
        payload["end"] = {"dateTime": f"{date}T{end}:00", "timeZone": TIMEZONE}
    else:
        next_day = (dt.date.fromisoformat(date) + dt.timedelta(days=1)).isoformat()
        payload["start"] = {"date": date}
        payload["end"] = {"date": next_day}
    return payload


def normalize_event(event: dict) -> dict:
    start, end = event.get("start") or {}, event.get("end") or {}
    ns = {"date": start["date"]} if "date" in start else {"dateTime": start.get("dateTime"), "timeZone": start.get("timeZone", TIMEZONE)}
    ne = {"date": end["date"]} if "date" in end else {"dateTime": end.get("dateTime"), "timeZone": end.get("timeZone", TIMEZONE)}
    reminders = event.get("reminders") or {}
    overrides = sorted((x.get("method"), x.get("minutes")) for x in reminders.get("overrides", []))
    private = (event.get("extendedProperties") or {}).get("private") or {}
    return {"summary": event.get("summary", ""), "description": event.get("description", ""), "start": ns, "end": ne, "reminders": {"useDefault": reminders.get("useDefault", False), "overrides": overrides}, "gh_agenda_issue": private.get("gh_agenda_issue")}


def upsert_event(token: str, issue: dict, meta: dict[str, str], key: str, date: str) -> bool:
    payload = event_payload(issue, meta, key, date)
    found = find_event(token, key)
    base = f"https://www.googleapis.com/calendar/v3/calendars/{urllib.parse.quote(CALENDAR_ID, safe='@')}/events"
    if found and found.get("status") != "cancelled":
        if normalize_event(found) == normalize_event(payload):
            print(f"EVENT NO_CHANGE {key}")
            return False
        request_json(f"{base}/{urllib.parse.quote(found['id'])}", method="PATCH", payload=payload, headers=auth(token))
        print(f"EVENT UPDATE {key}")
        return True
    request_json(base, method="POST", payload=payload, headers=auth(token))
    print(f"EVENT CREATE {key}")
    return True


def delete_event(token: str, event: dict) -> None:
    if event.get("status") == "cancelled":
        return
    url = f"https://www.googleapis.com/calendar/v3/calendars/{urllib.parse.quote(CALENDAR_ID, safe='@')}/events/{urllib.parse.quote(event['id'])}"
    request_json(url, method="DELETE", headers=auth(token))


def main() -> None:
    if not REPOSITORIES:
        die("GH_AGENDA_REPOSITORIES is empty")
    token = google_access_token()
    tasks = list_tasks(token)
    managed_count = task_changes = event_changes = 0
    for repo in REPOSITORIES:
        for issue in list_issues(repo):
            meta = parse_metadata(issue.get("body"))
            if not managed(meta):
                continue
            managed_count += 1
            assert meta is not None
            key = key_for(issue)
            date = chosen_date(meta)
            task = find_task(tasks, key)
            event = find_event(token, key)
            if issue.get("state") == "closed":
                if task and task.get("status") != "completed":
                    complete_task(token, task); task_changes += 1; print(f"TASK COMPLETE {key}")
                if event and event.get("status") != "cancelled":
                    delete_event(token, event); event_changes += 1; print(f"EVENT DELETE {key}")
                continue
            if date:
                if task:
                    delete_task(token, task); task_changes += 1; print(f"TASK DELETE {key}")
                if upsert_event(token, issue, meta, key, date):
                    event_changes += 1
            else:
                if event and event.get("status") != "cancelled":
                    delete_event(token, event); event_changes += 1; print(f"EVENT DELETE {key}")
                if upsert_task(token, tasks, issue, key):
                    task_changes += 1
    print(f"RESULT managed={managed_count} task_changes={task_changes} event_changes={event_changes}")


if __name__ == "__main__":
    main()
