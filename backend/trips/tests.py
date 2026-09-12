"""Unit tests for the HOS scheduler (no network needed)."""

from datetime import datetime, timezone
from unittest import mock

from django.test import TestCase

from .services.hos import (
    HosScheduler, summarize, build_daily_logs, DRIVING, OFF,
    MAX_DRIVE, MAX_WINDOW, DRIVE_BEFORE_BREAK, CYCLE_LIMIT, HOUR,
)

START = datetime(2026, 7, 23, 8, 0)


def make(leg1, leg2, cycle, mph=55):
    scheduler = HosScheduler(cycle_used_hours=cycle, avg_mph=mph, start_dt=START)
    scheduler.drive(leg1, "Drive to pickup")
    scheduler.on_duty(60, "Pickup")
    scheduler.drive(leg2, "Drive to drop-off")
    scheduler.on_duty(60, "Drop-off")
    return scheduler


class HosLimitTests(TestCase):
    def _assert_valid(self, scheduler):
        segments = scheduler.segments
        for prev_seg, next_seg in zip(segments, segments[1:]):
            self.assertEqual(prev_seg.end_min, next_seg.start_min)  # contiguous
        drive_run = window_start = since_break = 0
        for seg in segments:
            if seg.status == OFF and seg.duration >= 10 * HOUR:
                drive_run = since_break = 0
                window_start = seg.end_min
            if seg.status != DRIVING and seg.duration >= 30:
                since_break = 0
            if seg.status == DRIVING:
                drive_run += seg.duration
                since_break += seg.duration
                self.assertLessEqual(drive_run, MAX_DRIVE + 1)
                self.assertLessEqual(since_break, DRIVE_BEFORE_BREAK + 1)
                self.assertLessEqual(seg.end_min - window_start, MAX_WINDOW + 1)

    def test_short_trip_single_day(self):
        scheduler = make(10, 60, 0)
        self._assert_valid(scheduler)
        summary = summarize(scheduler.segments, 70, START)
        self.assertEqual(summary["num_days"], 1)
        self.assertEqual(summary["fuel_stops"], 0)

    def test_long_trip_multi_day(self):
        scheduler = make(120, 1500, 10)
        self._assert_valid(scheduler)
        summary = summarize(scheduler.segments, 1620, START)
        self.assertGreaterEqual(summary["num_days"], 3)
        self.assertGreaterEqual(summary["fuel_stops"], 1)

    def test_cycle_limit_forces_restart(self):
        scheduler = make(5, 120, 69.5)
        labels = " ".join(seg.label for seg in scheduler.segments)
        self.assertIn("34-hour restart", labels)

    def test_daily_logs_cover_all_time(self):
        scheduler = make(50, 800, 0)
        logs = build_daily_logs(scheduler.segments, START)
        for log in logs:
            total = sum(v for v in log["totals_min"].values())
            self.assertEqual(total, 24 * HOUR)


def _fake_geocode(query):
    lat, lon = {"A": (32.0, -97.0), "B": (34.0, -99.0), "C": (40.0, -105.0)}[query]
    return {"lat": lat, "lon": lon, "name": f"{query} full name",
            "short": f"{query}ville, TX"}


def _fake_route(points):
    n = 400
    return {
        "geometry": [[32.0 + 8.0 * i / n, -97.0 - 8.0 * i / n] for i in range(n + 1)],
        "distance_miles": 1200.0, "duration_hours": 20.0,
        "legs": [{"distance_miles": 200.0, "duration_hours": 10 / 3},
                 {"distance_miles": 1000.0, "duration_hours": 50 / 3}],
    }


@mock.patch("trips.services.geo.reverse_geocode",
            lambda lat, lon: f"Town {lat:.1f}, TX")
@mock.patch("trips.services.geo.route", _fake_route)
@mock.patch("trips.services.geo.geocode", _fake_geocode)
class PlannerTests(TestCase):
    """End-to-end planner output with geocoding/routing stubbed out."""

    def plan(self, cycle=0, start=START):
        from .services.planner import plan_trip
        return plan_trip("A", "B", "C", cycle, start_dt=start)

    def test_aware_start_datetime_is_accepted(self):
        result = self.plan(start=datetime(2026, 7, 23, 8, 0, tzinfo=timezone.utc))
        self.assertEqual(result["logs"][0]["date"], "2026-07-23")

    def test_remarks_mark_status_changes_with_a_place(self):
        for log in self.plan()["logs"]:
            pieces = log["segments"]
            for remark in log["remarks"]:
                self.assertTrue(remark["location"])
                idx = next(pos for pos, piece in enumerate(pieces)
                           if piece["start"] == remark["minute"])
                self.assertFalse(pieces[idx]["continued"])
                if idx:
                    self.assertNotEqual(pieces[idx - 1]["status"], pieces[idx]["status"])

    def test_known_stops_use_entered_names(self):
        result = self.plan()
        pickup_remarks = [remark for log in result["logs"] for remark in log["remarks"]
                          if remark["text"] == "Pickup"]
        self.assertEqual(pickup_remarks[0]["location"], "Bville, TX")
        self.assertEqual(result["logs"][0]["from"], "Aville, TX")
        self.assertEqual(result["logs"][-1]["to"], "Cville, TX")
        last_remark = result["logs"][-1]["remarks"][-1]
        self.assertEqual((last_remark["text"], last_remark["location"]),
                         ("Off duty (trip complete)", "Cville, TX"))

    def test_hos_numbers_after_restart(self):
        result = self.plan(cycle=65)
        self.assertIn("34-hour cycle restart",
                      [item["title"] for item in result["timeline"]])
        hos = result["hos"]
        self.assertLessEqual(hos["cycle_hours"], 70)
        self.assertGreater(hos["cycle_remaining"], 0)
        self.assertLessEqual(hos["drive_hours"], 11)
        self.assertLessEqual(hos["window_hours"], 14)
        self.assertTrue(any(log["recap"]["restart_completed"] for log in result["logs"]))

    def test_recap(self):
        logs = self.plan(cycle=20)["logs"]
        first_recap = logs[0]["recap"]
        self.assertAlmostEqual(first_recap["last_7_days"],
                               20 + first_recap["on_duty_today"], places=1)
        for log in logs:
            recap = log["recap"]
            self.assertAlmostEqual(recap["available_tomorrow"],
                                   max(0, 70 - recap["last_7_days"]), places=1)
            self.assertLessEqual(recap["last_5_days"], recap["last_7_days"])


SAMPLE_DOC = {
    "current_location": "Dallas, TX", "pickup_location": "Oklahoma City, OK",
    "dropoff_location": "Denver, CO", "current_cycle_used_hours": 10,
    "driver_name": "Anupam", "carrier_name": "DS",
    "total_miles": 780.0, "total_drive_hours": 13.0, "num_days": 2,
    "result": {"summary": {"total_miles": 780.0}, "logs": []},
}


class OrmRepositoryTests(TestCase):
    """The SQLite fallback used when MongoDB is not configured."""

    def setUp(self):
        from .repository import reset_repository
        reset_repository()

    def test_fallback_when_no_uri(self):
        from django.test import override_settings
        from .repository import get_repository, OrmTripRepository
        with override_settings(MONGODB_URI=""):
            repo = get_repository()
        self.assertIsInstance(repo, OrmTripRepository)

    def test_roundtrip(self):
        from .repository import OrmTripRepository
        repo = OrmTripRepository()
        tid = repo.save(dict(SAMPLE_DOC))
        self.assertTrue(tid)
        got = repo.get(tid)
        self.assertEqual(got["trip_id"], tid)
        listed = repo.list()
        self.assertEqual(listed[0]["driver_name"], "Anupam")
        self.assertIsNone(repo.get("999999"))


class MongoRepositoryTests(TestCase):
    """MongoTripRepository logic, exercised against an in-memory mongomock."""

    def _repo(self):
        import mongomock
        from .repository import MongoTripRepository
        return MongoTripRepository(mongomock.MongoClient())

    def test_roundtrip(self):
        repo = self._repo()
        tid = repo.save(dict(SAMPLE_DOC))
        self.assertTrue(tid)
        got = repo.get(tid)
        self.assertEqual(got["trip_id"], tid)
        self.assertEqual(got["summary"]["total_miles"], 780.0)

    def test_list_excludes_result_and_sorts(self):
        repo = self._repo()
        repo.save({**SAMPLE_DOC, "driver_name": "A"})
        repo.save({**SAMPLE_DOC, "driver_name": "B"})
        listed = repo.list()
        self.assertEqual(len(listed), 2)
        self.assertNotIn("result", listed[0])
        self.assertIn("total_miles", listed[0])

    def test_invalid_id_returns_none(self):
        self.assertIsNone(self._repo().get("not-an-objectid"))
