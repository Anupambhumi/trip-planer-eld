"""
FMCSA Hours-of-Service scheduler for a property-carrying driver on the
70-hour / 8-day cycle.

Rules modeled (per FMCSA Interstate Truck Driver's Guide to HOS, 2022):
  * 11-hour driving limit   -> max 11 h driving after 10 consecutive hours off.
  * 14-hour driving window   -> no driving after the 14th hour on duty (breaks
                                do NOT extend the window).
  * 30-minute break          -> required after 8 cumulative hours of driving;
                                satisfied by any 30 min of non-driving time.
  * 70-hour / 8-day limit    -> no driving after 70 on-duty hours in 8 days.
  * 34-hour restart          -> resets the 70-hour cycle.
  * 10-hour reset            -> restores the 11-hour and 14-hour clocks.

Assumptions (from the assessment brief):
  * Property-carrying driver, 70 hrs / 8 days, no adverse driving conditions.
  * Fueling at least once every 1,000 miles.
  * 1 hour on-duty for pickup and 1 hour on-duty for drop-off.

The scheduler is intentionally framework-free so it can be unit tested on its
own and reused from the Django view.
"""

from dataclasses import dataclass, field, asdict
from datetime import date, datetime, timedelta

# ---- Duty statuses (match the four rows of a paper log) --------------------
OFF = "OFF"          # 1. Off duty
SB = "SB"            # 2. Sleeper berth
DRIVING = "D"        # 3. Driving
ON = "ON"            # 4. On duty (not driving)

MIN = 1
HOUR = 60 * MIN

# ---- Limits (minutes) ------------------------------------------------------
MAX_DRIVE = 11 * HOUR            # 11-hour driving limit
MAX_WINDOW = 14 * HOUR           # 14-hour on-duty window
DRIVE_BEFORE_BREAK = 8 * HOUR    # driving allowed before a 30-min break
BREAK_LEN = 30 * MIN             # required break length
CYCLE_LIMIT = 70 * HOUR          # 70-hour / 8-day on-duty limit
DAILY_RESET = 10 * HOUR          # 10 consecutive hours off resets the day
RESTART_LEN = 34 * HOUR          # 34-hour restart resets the cycle

# ---- Task constants --------------------------------------------------------
PICKUP_MIN = 1 * HOUR
DROPOFF_MIN = 1 * HOUR
FUEL_MIN = 30 * MIN              # on-duty fueling stop
FUEL_EVERY_MILES = 1000.0


@dataclass
class Segment:
    """A contiguous block of one duty status on the continuous trip timeline."""
    status: str
    start_min: int          # minutes from trip start
    end_min: int
    label: str = ""         # human note (e.g. "Drive to pickup", "Fuel stop")
    start_mile: float = 0.0 # cumulative trip miles at segment start
    end_mile: float = 0.0
    location: str = ""      # "City, ST" at segment start (filled by planner)

    @property
    def duration(self):
        return self.end_min - self.start_min


class HosScheduler:
    def __init__(self, cycle_used_hours=0.0, avg_mph=55.0, start_dt=None):
        self.cycle_used = int(round(cycle_used_hours * HOUR))
        self.avg_mph = avg_mph if avg_mph and avg_mph > 0 else 55.0
        self.start_dt = start_dt or datetime.now().replace(
            hour=8, minute=0, second=0, microsecond=0)

        self.clock_min = 0      # current time cursor (minutes from start)
        self.mile = 0.0         # cumulative miles driven
        self.drive_today = 0    # driving minutes since last 10-h reset
        self.window_start = 0   # start of the current 14-h window
        self.since_break = 0    # driving minutes since last qualifying break
        self.next_fuel = FUEL_EVERY_MILES
        self.segments = []

    # -- low level ----------------------------------------------------------
    def _add(self, status, duration_min, label="", miles=0.0):
        if duration_min <= 0:
            return
        segment = Segment(status, self.clock_min, self.clock_min + duration_min,
                          label, self.mile, self.mile + miles)
        self.segments.append(segment)
        self.clock_min += duration_min
        self.mile += miles
        # Any 30+ min of non-driving satisfies the break requirement.
        if status != DRIVING and duration_min >= BREAK_LEN:
            self.since_break = 0
        if status in (OFF, SB):
            # Off-duty / sleeper does not add to the on-duty cycle.
            pass
        else:
            self.cycle_used += duration_min

    def _take_10h_reset(self):
        self._add(OFF, DAILY_RESET, "10-hour reset (sleeper/off duty)")
        self.drive_today = 0
        self.since_break = 0
        self.window_start = self.clock_min

    def _take_34h_restart(self):
        self._add(OFF, RESTART_LEN, "34-hour restart")
        self.cycle_used = 0
        self.drive_today = 0
        self.since_break = 0
        self.window_start = self.clock_min

    def _take_break(self):
        self._add(OFF, BREAK_LEN, "30-minute break")
        self.since_break = 0

    # -- public tasks -------------------------------------------------------
    def drive(self, miles, label="Driving"):
        """Drive `miles`, inserting any required rests along the way."""
        remaining_miles = miles
        while remaining_miles > 1e-6:
            window_elapsed = self.clock_min - self.window_start

            if self.cycle_used >= CYCLE_LIMIT:
                self._take_34h_restart()
                continue
            if self.drive_today >= MAX_DRIVE or window_elapsed >= MAX_WINDOW:
                self._take_10h_reset()
                continue
            if self.since_break >= DRIVE_BEFORE_BREAK:
                self._take_break()
                continue

            # Minutes of driving still permitted before some limit is hit.
            allowed_min = min(
                MAX_DRIVE - self.drive_today,
                MAX_WINDOW - window_elapsed,
                DRIVE_BEFORE_BREAK - self.since_break,
                CYCLE_LIMIT - self.cycle_used,
            )
            if allowed_min <= 0:
                # A limit was reached exactly; loop will insert the reset.
                continue

            # Miles we could cover in `allowed_min`, or before next fuel stop.
            miles_by_time = (allowed_min / HOUR) * self.avg_mph
            miles_to_fuel = self.next_fuel - self.mile
            chunk_miles = min(remaining_miles, miles_by_time, miles_to_fuel)
            chunk_min = int(round((chunk_miles / self.avg_mph) * HOUR))
            chunk_min = max(chunk_min, 1) if chunk_miles > 1e-6 else 0
            if chunk_min == 0:
                break

            self._add(DRIVING, chunk_min, label, miles=chunk_miles)
            self.drive_today += chunk_min
            self.since_break += chunk_min
            remaining_miles -= chunk_miles

            # Fuel stop when we reach a 1,000-mile boundary and still driving.
            if self.mile + 1e-6 >= self.next_fuel and remaining_miles > 1e-6:
                self.on_duty(FUEL_MIN, "Fuel stop")
                self.next_fuel += FUEL_EVERY_MILES

    def on_duty(self, duration_min, label="On duty"):
        """On-duty (not driving) work such as pickup, drop-off, fueling."""
        remaining_min = duration_min
        while remaining_min > 0:
            if self.cycle_used >= CYCLE_LIMIT:
                self._take_34h_restart()
                continue
            self._add(ON, remaining_min, label)
            remaining_min = 0


# ---------------------------------------------------------------------------
# Splitting the continuous timeline into calendar-day log sheets
# ---------------------------------------------------------------------------
STATUS_ROW = {OFF: 1, SB: 2, DRIVING: 3, ON: 4}
STATUS_NAME = {OFF: "Off Duty", SB: "Sleeper Berth", DRIVING: "Driving",
               ON: "On Duty (not driving)"}


def build_daily_logs(segments, start_dt):
    """Slice segments at midnight boundaries into per-day log sheets."""
    pieces_by_day = {}
    for segment in segments:
        abs_start = start_dt + timedelta(minutes=segment.start_min)
        abs_end = start_dt + timedelta(minutes=segment.end_min)
        cursor = abs_start
        while cursor < abs_end:
            day_key = cursor.date()
            midnight_next = datetime.combine(
                day_key, datetime.min.time()) + timedelta(days=1)
            piece_end = min(abs_end, midnight_next)
            day_pieces = pieces_by_day.setdefault(day_key, [])
            start_of_day = datetime.combine(day_key, datetime.min.time())
            day_pieces.append({
                "status": segment.status,
                "row": STATUS_ROW[segment.status],
                "start": int((cursor - start_of_day).total_seconds() // 60),
                "end": int((piece_end - start_of_day).total_seconds() // 60),
                "label": segment.label,
                "location": segment.location,
                # True for the part of a segment carried past midnight.
                "continued": cursor != abs_start,
            })
            cursor = piece_end

    last_day = max(pieces_by_day) if pieces_by_day else None
    logs = []
    for day_number, day_key in enumerate(sorted(pieces_by_day.keys()), start=1):
        day_pieces = sorted(pieces_by_day[day_key], key=lambda piece: piece["start"])
        # Fill any gaps (including before the first and after the last
        # segment) with off-duty time so every log covers a full 24 hours.
        day_pieces = _fill_day(day_pieces)
        if day_key == last_day and day_pieces[-1]["label"] == "":
            # The driver goes off duty once the drop-off is done.
            day_pieces[-1]["label"] = "Off duty (trip complete)"
            day_pieces[-1]["location"] = segments[-1].location
        totals = {OFF: 0, SB: 0, DRIVING: 0, ON: 0}
        remarks = []
        prev_status = None
        for piece in day_pieces:
            totals[piece["status"]] += piece["end"] - piece["start"]
            # A remark belongs at each change of duty status, not at the
            # midnight where a status simply carries over to a new sheet.
            if (piece["label"] and not piece["continued"]
                    and piece["status"] != prev_status):
                remarks.append({
                    "minute": piece["start"],
                    "time": _fmt(piece["start"]),
                    "text": piece["label"],
                    "location": piece["location"],
                })
            prev_status = piece["status"]
        logs.append({
            "day": day_number,
            "date": day_key.isoformat(),
            "segments": day_pieces,
            "totals_min": totals,
            "totals_hours": {status: round(minutes / HOUR, 2)
                             for status, minutes in totals.items()},
            "remarks": remarks,
        })
    return logs


def _fill_day(day_pieces, day_min=24 * HOUR):
    """Fill gaps before/between/after segments with off-duty to span 24 h."""
    filled = []
    cursor = 0
    for piece in day_pieces:
        if piece["start"] > cursor:
            filled.append({"status": OFF, "row": STATUS_ROW[OFF],
                           "start": cursor, "end": piece["start"], "label": "",
                           "location": "", "continued": False})
        filled.append(piece)
        cursor = max(cursor, piece["end"])
    if cursor < day_min:
        filled.append({"status": OFF, "row": STATUS_ROW[OFF],
                       "start": cursor, "end": day_min, "label": "",
                       "location": "", "continued": False})
    return filled


def _fmt(minutes):
    hours = (minutes // 60) % 24
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"


def summarize(segments, total_miles, start_dt):
    total_min = segments[-1].end_min if segments else 0
    drive_min = sum(seg.duration for seg in segments if seg.status == DRIVING)
    on_min = sum(seg.duration for seg in segments if seg.status == ON)
    off_min = sum(seg.duration for seg in segments if seg.status in (OFF, SB))
    fuel_stops = sum(1 for seg in segments if seg.label == "Fuel stop")
    resets = sum(1 for seg in segments
                 if "reset" in seg.label or "restart" in seg.label)
    breaks = sum(1 for seg in segments if seg.label == "30-minute break")
    return {
        "total_miles": round(total_miles, 1),
        "total_drive_hours": round(drive_min / HOUR, 2),
        "total_on_duty_hours": round((drive_min + on_min) / HOUR, 2),
        "total_off_hours": round(off_min / HOUR, 2),
        "total_elapsed_hours": round(total_min / HOUR, 2),
        "num_days": len(build_daily_logs(segments, start_dt)),
        "fuel_stops": fuel_stops,
        "ten_hour_resets": resets,
        "thirty_min_breaks": breaks,
    }


DAY = 24 * HOUR


def add_recap(logs, segments, start_dt, cycle_used_hours):
    """Fill each sheet's 70-hour / 8-day recap (A, B, C on the paper form).

    Only the total of the hours used before the trip is known, not which days
    they fell on, so they are counted inside every look-back window until a
    34-hour restart clears them -- the conservative reading, and the same one
    the scheduler uses.
    """
    restart_ends = [seg.end_min for seg in segments
                    if seg.label == "34-hour restart"]
    on_duty_spans = [(seg.start_min, seg.end_min) for seg in segments
                     if seg.status in (DRIVING, ON)]
    # Trip start, in minutes after midnight of the first log day.
    start_offset_min = start_dt.hour * HOUR + start_dt.minute

    for log in logs:
        day_index = (date.fromisoformat(log["date"]) - start_dt.date()).days
        day_end = (day_index + 1) * DAY - start_offset_min  # min from trip start
        finished_restarts = [end for end in restart_ends if end <= day_end]
        last_restart_end = finished_restarts[-1] if finished_restarts else None

        def on_duty_hours(days_back):
            window_start = (day_index + 1 - days_back) * DAY - start_offset_min
            if last_restart_end is not None:
                window_start = max(window_start, last_restart_end)
            minutes = sum(max(0, min(span_end, day_end) - max(span_start, window_start))
                          for span_start, span_end in on_duty_spans)
            prior_hours = 0.0 if last_restart_end is not None else cycle_used_hours
            return minutes / HOUR + prior_hours

        last_7_days = on_duty_hours(7)
        log["recap"] = {
            "on_duty_today": round(log["totals_hours"][DRIVING]
                                   + log["totals_hours"][ON], 2),
            "last_7_days": round(last_7_days, 2),
            "available_tomorrow": round(
                max(0.0, CYCLE_LIMIT / HOUR - last_7_days), 2),
            "last_5_days": round(on_duty_hours(5), 2),
            "restart_completed": (last_restart_end is not None
                                  and last_restart_end > day_end - DAY),
        }


def shift_peaks(segments):
    """Most driving, and most of the 14-hour window used, in any one shift.

    A shift ends at any rest of 10+ consecutive hours. The window runs from
    the first on-duty minute to the end of the shift's last driving, which is
    exactly what the 14-hour rule limits.
    """
    peak_drive = peak_window = 0
    shift_drive, shift_start = 0, None
    for seg in segments:
        if seg.status in (OFF, SB) and seg.duration >= DAILY_RESET:
            shift_drive, shift_start = 0, None
            continue
        if seg.status in (DRIVING, ON) and shift_start is None:
            shift_start = seg.start_min
        if seg.status == DRIVING:
            shift_drive += seg.duration
            peak_drive = max(peak_drive, shift_drive)
            peak_window = max(peak_window, seg.end_min - shift_start)
    return peak_drive / HOUR, peak_window / HOUR
