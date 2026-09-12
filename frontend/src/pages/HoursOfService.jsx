import React from "react";
import { Link } from "react-router-dom";
import { useTrip } from "../context/TripContext";
import Gauge from "../components/Gauge";
import Timeline from "../components/Timeline";

export default function HoursOfService() {
  const { trip } = useTrip();
  if (!trip) return (
    <div className="page">
      <div className="card empty">
        <h3>No active trip</h3>
        <p>Plan a trip to see the HOS breakdown.</p>
        <Link to="/plan" className="btn" style={{ marginTop: 14 }}>Plan a Trip</Link>
      </div>
    </div>
  );

  const hoursOfService = trip.hos;
  const cycleColor = hoursOfService.cycle_remaining <= 0 ? "#f5a524" : "#38bdf8";

  return (
    <div className="page">
      <h1 className="page-title">HOS Timeline</h1>
      <p className="page-sub">Duty status breakdown and event timeline for the active trip.</p>

      <div className="grid gauge-grid">
        <Gauge value={hoursOfService.window_hours} max={hoursOfService.window_limit} label="14-Hour Window" desc="Duty period" />
        <Gauge value={hoursOfService.drive_hours} max={hoursOfService.drive_limit} label="11-Hour Drive" desc="Driving limit" />
        <Gauge value={hoursOfService.cycle_hours} max={hoursOfService.cycle_limit} color={cycleColor} label="70-Hour Cycle" desc="8-day rolling" />
        <Gauge value={hoursOfService.cycle_remaining} max={hoursOfService.cycle_limit} label="Cycle Remaining" desc="Available hours" />
      </div>

      <div className="grid info-grid" style={{ marginTop: 22 }}>
        <div className="card info-card">
          <div className="k">Current Duty Status</div>
          <div className="v">{hoursOfService.current_status}</div>
          {hoursOfService.current_note && <span className="pill">{hoursOfService.current_note}</span>}
        </div>
        <div className="card info-card">
          <div className="k">30-Min Break</div>
          <div className="v">Required Breaks Taken</div>
          <span className="pill">{hoursOfService.breaks_taken} breaks</span>
        </div>
        <div className="card info-card">
          <div className="k">Fuel Stops</div>
          <div className="v">{hoursOfService.fuel_stops} Scheduled</div>
          <span className="pill">Every 1,000 mi</span>
        </div>
      </div>

      <div style={{ marginTop: 22 }}>
        <Timeline items={trip.timeline} title="Duty Status Timeline" />
      </div>
    </div>
  );
}
