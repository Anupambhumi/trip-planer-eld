import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { listTrips, getTrip } from "../apiClient";
import { useTrip } from "../context/TripContext";
import { IconCalendar, IconPin, IconArrow, IconRoute, IconFile } from "../components/Icons";

function fmtDate(iso) {
  try {
    return new Date(iso).toLocaleString("en-US", {
      month: "short", day: "numeric", year: "numeric",
      hour: "2-digit", minute: "2-digit",
    });
  } catch { return iso; }
}
const short = (s) => (s || "").split(",").slice(0, 2).join(",");

export default function Trips() {
  const [trips, setTrips] = useState(null);
  const [error, setError] = useState("");
  const { trip: active, setTrip } = useTrip();
  const nav = useNavigate();
  const activeId = active?.trip_id;

  useEffect(() => {
    listTrips().then(setTrips).catch((e) => setError(e.message));
  }, []);

  const open = async (id) => {
    try {
      const full = await getTrip(id);
      setTrip({ ...full, trip_id: id });
      nav("/");
    } catch (e) { setError(e.message); }
  };

  return (
    <div className="page">
      <h1 className="page-title">All Trips</h1>
      <p className="page-sub">Browse every planned trip saved in the database. Click a trip to load it on the dashboard.</p>

      {error && <div className="error">{error}</div>}
      {!trips && !error && <div className="empty">Loading trips…</div>}
      {trips && trips.length === 0 && (
        <div className="card empty"><h3>No trips yet</h3><p>Plan your first trip from the Plan tab.</p></div>
      )}

      <div className="grid trip-grid">
        {trips?.map((t) => (
          <div className="trip-card" key={t.id} onClick={() => open(t.id)}>
            <span className="trip-arrow"><IconArrow size={20} /></span>
            <div className="trip-top">
              {activeId === t.id && <span className="badge-active">Active</span>}
              <IconCalendar size={15} /> {fmtDate(t.created_at)}
            </div>
            <div className="trip-loc"><IconPin size={17} className="ico" /> {short(t.current_location)}</div>
            <div className="trip-loc sub">→ {short(t.pickup_location)}</div>
            <div className="trip-loc"><span style={{ width: 17 }} />→ {short(t.dropoff_location)}</div>
            <div className="trip-foot">
              <span><IconRoute size={15} className="ico" /> {Math.round(t.total_miles).toLocaleString()} mi</span>
              <span><IconFile size={15} className="ico" /> {t.num_days} log sheets</span>
              {t.driver_name && <span>Driver: {t.driver_name}</span>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
