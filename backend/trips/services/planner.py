"""
Trip planner: ties geocoding + routing + the HOS scheduler together and
produces the full payload the frontend needs (route, stops, timeline, charts,
HOS gauges, and drawn daily logs).
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta

from . import geo
from .hos import (
    HosScheduler, build_daily_logs, add_recap, shift_peaks, summarize,
    DRIVING, ON, OFF, SB, PICKUP_MIN, DROPOFF_MIN, HOUR, DAY,
)

STATUS_LABEL = {OFF: "Off duty", SB: "Sleeper berth", DRIVING: "Driving",
                ON: "On duty (not driving)"}


def plan_trip(current, pickup, dropoff, cycle_used_hours, start_dt=None,
              log_header=None):
    start_dt = start_dt or datetime.now().replace(
        hour=8, minute=0, second=0, microsecond=0)
    if start_dt.tzinfo is not None:
        # Log sheets use wall-clock time at the home terminal; drop the offset
        # so naive and aware datetimes are never mixed further down.
        start_dt = start_dt.replace(tzinfo=None)
    log_header = log_header or {}

    # 1. Geocode + route current -> pickup -> dropoff.
    start_geo = geo.geocode(current)
    pickup_geo = geo.geocode(pickup)
    dropoff_geo = geo.geocode(dropoff)
    route_info = geo.route([start_geo, pickup_geo, dropoff_geo])
    geometry = route_info["geometry"]
    cum_miles = geo.cumulative_miles(geometry)
    leg1_miles = route_info["legs"][0]["distance_miles"]
    leg2_miles = route_info["legs"][1]["distance_miles"]
    total_miles = route_info["distance_miles"]
    avg_mph = (total_miles / route_info["duration_hours"]
               if route_info["duration_hours"] > 0 else 55.0)

    # Trip miles come from OSRM's road distance, which differs slightly from
    # the length of the drawn geometry; scale when placing a mile on the line.
    geometry_scale = cum_miles[-1] / total_miles if total_miles > 0 else 1.0

    def point_on_route(mile):
        return geo.point_at_mile(geometry, cum_miles, mile * geometry_scale)

    # 2. Run the HOS scheduler.
    scheduler = HosScheduler(cycle_used_hours=cycle_used_hours,
                             avg_mph=avg_mph, start_dt=start_dt)
    scheduler.drive(leg1_miles, "Drive to pickup")
    scheduler.on_duty(PICKUP_MIN, "Pickup")
    scheduler.drive(leg2_miles, "Drive to drop-off")
    scheduler.on_duty(DROPOFF_MIN, "Drop-off")
    segments = scheduler.segments
    end_min = segments[-1].end_min

    # 3. Name the place of every duty-status change (the log's remarks must
    #    show city + state) and of each day's start and end (From / To).
    start_offset_min = start_dt.hour * HOUR + start_dt.minute
    trip_span = (start_dt + timedelta(minutes=end_min)).date() - start_dt.date()
    day_mile_spans = {}
    for day_index in range(trip_span.days + 1):
        day_start_min = max(0, day_index * DAY - start_offset_min)
        day_end_min = min(end_min, (day_index + 1) * DAY - start_offset_min)
        day_key = (start_dt.date() + timedelta(days=day_index)).isoformat()
        day_mile_spans[day_key] = (
            round(_mile_at(segments, day_start_min), 1),
            round(_mile_at(segments, day_end_min), 1))
    mile_marks = {round(seg.start_mile, 1) for seg in segments}
    for mile_span in day_mile_spans.values():
        mile_marks.update(mile_span)
    place_by_mile = _place_names(mile_marks, point_on_route, {
        0.0: start_geo["short"],
        leg1_miles: pickup_geo["short"],
        total_miles: dropoff_geo["short"],
    })
    for seg in segments:
        seg.location = place_by_mile[round(seg.start_mile, 1)]

    # 4. Geo-located stops.
    stops = [
        _stop("start", "Current location", start_geo, 0.0, start_dt, 0),
        _stop("pickup", "Pickup", pickup_geo, leg1_miles, start_dt,
              _event_minute(segments, "Pickup")),
        _stop("dropoff", "Drop-off", dropoff_geo, total_miles, start_dt,
              _event_minute(segments, "Drop-off")),
    ]
    for seg in segments:
        if seg.status == DRIVING or seg.label in ("Pickup", "Drop-off"):
            continue
        coords = point_on_route(seg.start_mile)
        stops.append({
            "type": _classify(seg.label),
            "label": seg.label,
            "place": seg.location,
            "lat": coords[0] if coords else None,
            "lon": coords[1] if coords else None,
            "mile": round(seg.start_mile, 1),
            "arrive_time": _clock(start_dt, seg.start_min),
            "duration_min": seg.duration,
        })
    stops.sort(key=lambda stop: stop["mile"])

    # 5. Timeline of every segment (for Route + HOS pages).
    timeline = _build_timeline(segments, start_dt, start_geo["short"],
                               pickup_geo["short"], dropoff_geo["short"],
                               leg1_miles)

    # 6. Daily logs, enriched with per-day miles, From / To, header + recap.
    logs = build_daily_logs(segments, start_dt)
    miles_by_date = _miles_by_date(segments, start_dt)
    for log in logs:
        log["total_miles_today"] = round(miles_by_date.get(log["date"], 0.0), 1)
        from_mile, to_mile = day_mile_spans.get(log["date"], (0.0, 0.0))
        log["from"] = place_by_mile.get(from_mile, "")
        log["to"] = place_by_mile.get(to_mile, "")
        log["header"] = log_header
    add_recap(logs, segments, start_dt, cycle_used_hours)
    summary = summarize(segments, total_miles, start_dt)

    # 7. Charts + HOS gauges. The scheduler's own cycle counter is the truth:
    #    it includes the hours used before the trip and resets on a restart.
    cycle_end_hours = scheduler.cycle_used / HOUR
    charts = _build_charts(logs, segments, stops, cycle_end_hours)
    hos = _build_hos(segments, cycle_end_hours)

    return {
        "inputs": {
            "current_location": start_geo["name"],
            "pickup_location": pickup_geo["name"],
            "dropoff_location": dropoff_geo["name"],
            "current_cycle_used_hours": cycle_used_hours,
            "log_header": log_header,
        },
        "route": {
            "geometry": geometry,
            "distance_miles": round(total_miles, 1),
            "duration_hours": round(route_info["duration_hours"], 2),
            "avg_mph": round(avg_mph, 1),
            "pickup_mile": round(leg1_miles, 1),
        },
        "stops": stops,
        "timeline": timeline,
        "summary": summary,
        "charts": charts,
        "hos": hos,
        "logs": logs,
        "start_datetime": start_dt.isoformat(),
    }


# --------------------------------------------------------------------------
def _mile_at(segments, minute):
    """Trip mileage at `minute`, interpolating inside driving segments."""
    for seg in segments:
        if seg.start_min <= minute <= seg.end_min:
            if seg.status == DRIVING and seg.duration:
                fraction = (minute - seg.start_min) / seg.duration
                return seg.start_mile + fraction * (seg.end_mile - seg.start_mile)
            return seg.start_mile
    return segments[-1].end_mile if segments else 0.0


def _place_names(mile_marks, point_on_route, known_places):
    """Map route miles to "City, ST", reverse-geocoding the rest in parallel.

    `known_places` maps the miles of the geocoded trip stops to their names,
    so the start, pickup and drop-off always read exactly as entered.
    """
    place_by_mile, pending = {}, {}
    for mile in mile_marks:
        match = next((name for known_mile, name in known_places.items()
                      if abs(mile - known_mile) < 0.5), None)
        if match:
            place_by_mile[mile] = match
        else:
            pending[mile] = point_on_route(mile)

    def lookup(coords):
        return geo.reverse_geocode(coords[0], coords[1]) if coords else None

    if pending:
        # Photon's public server starts refusing (503) at ~10 concurrent calls.
        with ThreadPoolExecutor(max_workers=4) as pool:
            for mile, name in zip(pending, pool.map(lookup, pending.values())):
                place_by_mile[mile] = name or f"Mile {mile:,.0f} of route"
    return place_by_mile


def _build_timeline(segments, start_dt, start_name, pickup_name, dropoff_name,
                    leg1_miles):
    items = []
    for seg in segments:
        abs_start = start_dt + timedelta(minutes=seg.start_min)
        abs_end = start_dt + timedelta(minutes=seg.end_min)
        note = seg.label
        if seg.status == DRIVING:
            if seg.start_mile < leg1_miles - 1e-6:
                note = f"En route {start_name} → {pickup_name}"
            else:
                note = f"En route {pickup_name} → {dropoff_name}"
        items.append({
            "status": seg.status,
            "status_label": STATUS_LABEL[seg.status],
            "title": _timeline_title(seg),
            "start_iso": abs_start.isoformat(),
            "end_iso": abs_end.isoformat(),
            "start_str": abs_start.strftime("%b %d, %Y, %I:%M %p"),
            "end_str": abs_end.strftime("%b %d, %Y, %I:%M %p"),
            "duration_min": seg.duration,
            "duration_str": _dur(seg.duration),
            "miles": round(seg.end_mile - seg.start_mile, 0) if seg.status == DRIVING else 0,
            "location": seg.location,
            "note": note,
        })
    return items


def _timeline_title(seg):
    if seg.status == DRIVING:
        return "Driving"
    if "34-hour" in seg.label:
        return "34-hour cycle restart"
    if "10-hour" in seg.label:
        return "10-hour reset"
    if "30-minute" in seg.label:
        return "30-minute break"
    if seg.label == "Fuel stop":
        return "Fuel stop"
    if seg.label in ("Pickup", "Drop-off"):
        return seg.label
    return STATUS_LABEL[seg.status]


def _build_charts(logs, segments, stops, cycle_end_hours):
    driving_by_day = [{"date": log["date"], "hours": log["totals_hours"][DRIVING]}
                      for log in logs]
    trip_progress = [{"date": log["date"],
                      "miles": log["total_miles_today"]} for log in logs]

    drive_hours = sum(seg.duration for seg in segments if seg.status == DRIVING) / HOUR
    on_duty_hours = sum(seg.duration for seg in segments if seg.status == ON) / HOUR
    off_duty_hours = sum(seg.duration for seg in segments
                         if seg.status in (OFF, SB)) / HOUR

    fuel_stops = [stop for stop in stops if stop["type"] == "fuel"]
    fuel_chart = [{"label": f"Stop {number}", "mile": stop["mile"]}
                  for number, stop in enumerate(fuel_stops, start=1)]

    return {
        "driving_by_day": driving_by_day,
        "trip_progress": trip_progress,
        "duty_breakdown": {
            "driving": round(drive_hours, 1),
            "on_duty": round(on_duty_hours, 1),
            "off_duty": round(off_duty_hours, 1),
        },
        "cycle_usage": {
            "used": round(min(cycle_end_hours, 70), 1),
            "remaining": round(max(0.0, 70 - cycle_end_hours), 1),
            "limit": 70,
        },
        "fuel_stops": fuel_chart,
    }


def _build_hos(segments, cycle_end_hours):
    peak_drive, peak_window = shift_peaks(segments)
    breaks = sum(1 for seg in segments if seg.label == "30-minute break")
    resets = sum(1 for seg in segments
                 if "reset" in seg.label or "restart" in seg.label)
    fuel_stops = sum(1 for seg in segments if seg.label == "Fuel stop")
    current_status = STATUS_LABEL[segments[-1].status] if segments else "Off duty"
    current_note = segments[-1].label if segments else ""
    return {
        "window_hours": round(peak_window, 1),
        "window_limit": 14,
        "drive_hours": round(peak_drive, 1),
        "drive_limit": 11,
        "cycle_hours": round(cycle_end_hours, 1),
        "cycle_limit": 70,
        "cycle_remaining": round(max(0.0, 70 - cycle_end_hours), 1),
        "breaks_taken": breaks,
        "resets": resets,
        "fuel_stops": fuel_stops,
        "current_status": current_status.upper(),
        "current_note": current_note.upper(),
    }


def _miles_by_date(segments, start_dt):
    miles_per_day = {}
    for seg in segments:
        if seg.status != DRIVING or seg.end_mile <= seg.start_mile:
            continue
        abs_start = start_dt + timedelta(minutes=seg.start_min)
        abs_end = start_dt + timedelta(minutes=seg.end_min)
        total_seconds = (abs_end - abs_start).total_seconds() or 1
        seg_miles = seg.end_mile - seg.start_mile
        cursor = abs_start
        while cursor < abs_end:
            day_key = cursor.date().isoformat()
            midnight_next = datetime.combine(
                cursor.date(), datetime.min.time()) + timedelta(days=1)
            piece_end = min(abs_end, midnight_next)
            fraction = (piece_end - cursor).total_seconds() / total_seconds
            miles_per_day[day_key] = miles_per_day.get(day_key, 0.0) + seg_miles * fraction
            cursor = piece_end
    return miles_per_day


def _stop(kind, label, geo_point, mile, start_dt, minute):
    return {
        "type": kind, "label": label, "place": geo_point["short"],
        "lat": geo_point["lat"], "lon": geo_point["lon"], "name": geo_point["name"],
        "mile": round(mile, 1), "arrive_time": _clock(start_dt, minute),
    }


def _classify(label):
    text = label.lower()
    if "fuel" in text:
        return "fuel"
    if "34" in text or "restart" in text:
        return "restart"
    if "reset" in text:
        return "rest"
    if "break" in text:
        return "break"
    return "stop"


def _event_minute(segments, label):
    for seg in segments:
        if seg.label == label:
            return seg.start_min
    return 0


def _clock(start_dt, minute):
    return (start_dt + timedelta(minutes=minute)).strftime("%Y-%m-%d %H:%M")


def _dur(minutes):
    return f"{minutes // 60}h {minutes % 60:02d}m"
