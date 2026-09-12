import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useTrip } from "../context/TripContext";
import LogSheet from "../components/LogSheet";
import {
  IconZoomIn, IconZoomOut, IconExpand, IconPrint, IconPdf,
  IconChevron, IconChevronLeft,
} from "../components/Icons";

const hm = (h) => `${Math.floor(h)}h ${Math.round((h % 1) * 60).toString().padStart(2, "0")}m`;
const short = (s) => (s || "").split(",").slice(0, 3).join(",");

export default function Logs() {
  const { trip } = useTrip();
  const [page, setPage] = useState(0);
  const [scale, setScale] = useState(1);

  if (!trip) return (
    <div className="page">
      <div className="card empty">
        <h3>No active trip</h3>
        <p>Plan a trip to generate ELD daily log sheets.</p>
        <Link to="/plan" className="btn" style={{ marginTop: 14 }}>Plan a Trip</Link>
      </div>
    </div>
  );

  const logs = trip.logs;
  const log = logs[page];
  const s = trip.summary;
  const header = trip.inputs.log_header || {};

  return (
    <div className="page">
      <h1 className="page-title">ELD Logs</h1>
      <p className="page-sub">FMCSA daily log sheets for the active trip.</p>

      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
          <h2 className="card-h" style={{ margin: 0 }}>
            Log Sheet — {log.date} <span style={{ color: "var(--muted)", fontWeight: 500, fontSize: 15 }}>({page + 1} of {logs.length})</span>
          </h2>
          <div className="log-toolbar">
            <button onClick={() => setScale((v) => Math.max(0.6, +(v - 0.1).toFixed(2)))} title="Zoom out"><IconZoomOut size={18} /></button>
            <span className="pct">{Math.round(scale * 100)}%</span>
            <button onClick={() => setScale((v) => Math.min(2, +(v + 0.1).toFixed(2)))} title="Zoom in"><IconZoomIn size={18} /></button>
            <button onClick={() => setScale(1)} title="Fit"><IconExpand size={18} /></button>
            <button onClick={() => window.print()} title="Save as PDF"><IconPdf size={18} /></button>
            <button onClick={() => window.print()} title="Print"><IconPrint size={18} /></button>
          </div>
        </div>

        {/* Keyed by date so switching sheets replays the entrance animation. */}
        <div className="log-paper" key={log.date} style={{ marginTop: 16 }}>
          <LogSheet log={log} scale={scale} />
        </div>

        <div className="pager">
          <button className="btn btn-ghost" disabled={page === 0} onClick={() => setPage((p) => p - 1)}>
            <IconChevronLeft size={16} /> Previous
          </button>
          <div className="dots">
            {logs.map((_, i) => (
              <i key={i} className={i === page ? "on" : ""} onClick={() => setPage(i)} style={{ cursor: "pointer" }} />
            ))}
          </div>
          <button className="btn btn-ghost" disabled={page === logs.length - 1} onClick={() => setPage((p) => p + 1)}>
            Next <IconChevron size={16} />
          </button>
        </div>
      </div>

      <div className="card" style={{ marginTop: 22 }}>
        <h2 className="card-h">Trip Summary</h2>
        <Row k="Route" v={`${short(trip.inputs.current_location)} → ${short(trip.inputs.dropoff_location)}`} />
        <Row k="Distance" v={`${s.total_miles.toLocaleString()} mi`} />
        <Row k="Driving time" v={hm(s.total_drive_hours)} />
        <Row k="Total trip time" v={hm(s.total_elapsed_hours)} />
        <Row k="Fuel stops" v={s.fuel_stops} />
        <Row k="Log sheets" v={s.num_days} />
        <Row k="Driver" v={header.driver_name || "—"} />
        <Row k="Carrier" v={header.carrier_name || "—"} />
      </div>
    </div>
  );
}

const Row = ({ k, v }) => (
  <div className="review-row"><span className="k">{k}</span><span className="v">{v}</span></div>
);
