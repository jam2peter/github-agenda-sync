import importlib.util
import pathlib
import unittest

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
            "summary": "Example",
            "description": "Desc",
            "start": {"date": "2026-09-20"},
            "end": {"date": "2026-09-21"},
            "reminders": {"useDefault": False, "overrides": [{"method": "popup", "minutes": 5}]},
            "extendedProperties": {"private": {"gh_agenda_issue": "github:acme/repo#7"}},
        }
        richer = dict(base)
        richer["id"] = "google-generated-id"
        richer["etag"] = "etag"
        self.assertEqual(mod.normalize_event(base), mod.normalize_event(richer))


if __name__ == "__main__":
    unittest.main()
