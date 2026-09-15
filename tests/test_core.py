import importlib.util
import pathlib
import unittest
from unittest.mock import patch

MODULE_PATH = pathlib.Path(__file__).resolve().parents[1] / "src" / "github_agenda_sync.py"
spec = importlib.util.spec_from_file_location("github_agenda_sync", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


class CoreTests(unittest.TestCase):
    def test_parse_metadata(self):
        body = """x\n<!-- GH_AGENDA_SYNC\nmanaged=true\nstart_date=2026-09-20\ncalendar_start=09:00\n-->\ny"""
        meta = mod.parse_metadata(body)
        self.assertEqual(meta["managed"], "true")
        self.assertEqual(meta["start_date"], "2026-09-20")
        self.assertEqual(meta["calendar_start"], "09:00")

    def test_managed(self):
        self.assertTrue(mod.managed({"managed": "true"}))
        self.assertFalse(mod.managed({}))
        self.assertFalse(mod.managed({"managed": "false"}))

    def test_chosen_date_prefers_start_date(self):
        meta = {"start_date": "2026-09-20", "target_date": "2026-09-30"}
        self.assertEqual(mod.chosen_date(meta), "2026-09-20")

    def test_chosen_date_ignores_invalid(self):
        self.assertIsNone(mod.chosen_date({"start_date": "20/09/2026"}))

    def test_all_day_event_payload(self):
        issue = {"title": "Example", "_repo": "acme/repo", "number": 7, "html_url": "https://github.com/acme/repo/issues/7"}
        payload = mod.event_payload(issue, {}, "github:acme/repo#7", "2026-09-20")
        self.assertEqual(payload["start"], {"date": "2026-09-20"})
        self.assertEqual(payload["end"], {"date": "2026-09-21"})

    def test_normalize_event_ignores_unmanaged_fields(self):
        base = {
            "summary": "Example", "description": "Desc",
            "start": {"date": "2026-09-20"}, "end": {"date": "2026-09-21"},
            "reminders": {"useDefault": False, "overrides": [{"method": "popup", "minutes": 5}]},
            "extendedProperties": {"private": {"gh_agenda_issue": "github:acme/repo#7"}},
        }
        richer = dict(base, id="google-generated-id", etag="etag")
        self.assertEqual(mod.normalize_event(base), mod.normalize_event(richer))

    def test_task_payload_contains_stable_key(self):
        issue = {"title": "Example", "_repo": "acme/repo", "number": 7, "html_url": "https://github.com/acme/repo/issues/7"}
        payload = mod.task_payload(issue, mod.key_for(issue))
        self.assertIn("[GH_AGENDA_SYNC:github:acme/repo#7]", payload["notes"])

    def test_timed_event_defaults_end_time(self):
        issue = {"title": "Example", "_repo": "acme/repo", "number": 7, "html_url": "https://github.com/acme/repo/issues/7"}
        payload = mod.event_payload(issue, {"calendar_start": "09:30"}, "github:acme/repo#7", "2026-09-20")
        self.assertTrue(payload["start"]["dateTime"].endswith("T09:30:00"))
        self.assertTrue(payload["end"]["dateTime"].endswith("T10:30:00"))

    @patch.object(mod, "request_json")
    def test_upsert_task_is_idempotent(self, request):
        issue = {"title": "Example", "_repo": "acme/repo", "number": 7, "html_url": "https://github.com/acme/repo/issues/7"}
        key = mod.key_for(issue)
        existing = dict(mod.task_payload(issue, key), id="t1")
        changed = mod.upsert_task("token", [existing], issue, key)
        self.assertFalse(changed)
        request.assert_not_called()

    @patch.object(mod, "request_json")
    @patch.object(mod, "find_event")
    def test_upsert_event_is_idempotent(self, find_event, request):
        issue = {"title": "Example", "_repo": "acme/repo", "number": 7, "html_url": "https://github.com/acme/repo/issues/7"}
        key = mod.key_for(issue)
        existing = dict(mod.event_payload(issue, {}, key, "2026-09-20"), id="e1", status="confirmed")
        find_event.return_value = existing
        changed = mod.upsert_event("token", issue, {}, key, "2026-09-20")
        self.assertFalse(changed)
        request.assert_not_called()


if __name__ == "__main__":
    unittest.main()
