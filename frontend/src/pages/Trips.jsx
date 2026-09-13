import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { listTrips, getTrip } from "../apiClient";
import { useTrip, loadHistory } from "../context/TripContext";
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

function routeKey(trip) {
  return [
    (trip.current_location || "").split(",")[0].trim().toLowerCase(),
    (trip.pickup_location || "").split(",")[0].trim().toLowerCase(),
    (trip.dropoff_location || "").split(",")[0].trim().toLowerCase(),
    String(trip.created_at || "").slice(0, 16),
  ].join("|");
}

function mergeTrips(remote, local) {
  const out = [];
  const seenIds = new Set();
  const seenRoutes = new Set();

  const push = (trip) => {
    const id = String(trip.id || trip.server_id || "");
    const route = routeKey(trip);
    if (id && seenIds.has(id)) return;
    if (route !== "|||" && seenRoutes.has(route)) return;
    if (id) seenIds.add(id);
    if (trip.server_id) seenIds.add(String(trip.server_id));
    if (route !== "|||") seenRoutes.add(route);
    out.push(trip);
  };

  (local || []).forEach(push);
  (remote || []).forEach((trip) => push({ ...trip, server_id: trip.id }));
  return out.sort((a, b) => String(b.created_at || "").localeCompare(String(a.created_at || "")));
}

export default function Trips() {
  const [trips, setTrips] = useState(null);
  const [error, setError] = useState("");
  const { trip: active, setTrip, history } = useTrip();
  const nav = useNavigate();
  const activeId = active?.local_id || active?.trip_id;

  useEffect(() => {
    const local = history?.length ? history : loadHistory();
    listTrips()
      .then((remote) => setTrips(mergeTrips(remote, local)))
      .catch((e) => {
        if (local.length) setTrips(local);
        else setError(e.message);
      });
  }, [history]);

  const open = async (item) => {
    try {
      let full = item.result;
      if (!full && item.server_id) {
        full = await getTrip(item.server_id);
      } else if (!full) {
        full = await getTrip(item.id);
      }
      setTrip({
        ...full,
        trip_id: full.trip_id || item.server_id || item.id,
        local_id: item.id?.startsWith?.("local-") ? item.id : (full.local_id || item.id),
        saved_at: item.created_at,
        server_id: item.server_id,
      });
      nav("/");
    } catch (e) { setError(e.message); }
  };

  return (
    <div className="page">
      <h1 className="page-title">All Trips</h1>
      <p className="page-sub">
        Browse planned trips from this browser and the saved database.
        {trips?.length ? ` ${trips.length} trip${trips.length === 1 ? "" : "s"} saved.` : " Click a trip to load it on the dashboard."}
      </p>

      {error && <div className="error">{error}</div>}
      {!trips && !error && <div className="empty">Loading trips…</div>}
      {trips && trips.length === 0 && (
        <div className="card empty"><h3>No trips yet</h3><p>Plan your first trip from the Plan tab.</p></div>
      )}

      <div className="grid trip-grid">
        {trips?.map((t) => (
          <div className="trip-card" key={t.id} onClick={() => open(t)}>
            <span className="trip-arrow"><IconArrow size={20} /></span>
            <div className="trip-top">
              {String(activeId) === String(t.id) && <span className="badge-active">Active</span>}
              <IconCalendar size={15} /> {fmtDate(t.created_at)}
            </div>
            <div className="trip-loc"><IconPin size={17} className="ico" /> {short(t.current_location)}</div>
            <div className="trip-loc sub">→ {short(t.pickup_location)}</div>
            <div className="trip-loc"><span style={{ width: 17 }} />→ {short(t.dropoff_location)}</div>
            <div className="trip-foot">
              <span><IconRoute size={15} className="ico" /> {Math.round(t.total_miles || 0).toLocaleString()} mi</span>
              <span><IconFile size={15} className="ico" /> {t.num_days || 0} log sheets</span>
              {t.driver_name && <span>Driver: {t.driver_name}</span>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
