import React, { createContext, useContext, useState } from "react";

const TripContext = createContext(null);
const ACTIVE_KEY = "trippilot.activeTrip";
const HISTORY_KEY = "trippilot.tripHistory";
const HISTORY_LIMIT = 25;

function loadJson(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

function writeJson(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch {
    return false;
  }
}

function toHistoryEntry(result) {
  const inputs = result.inputs || {};
  const summary = result.summary || {};
  const header = inputs.log_header || {};
  const localId = result.local_id || result.trip_id || `local-${Date.now()}`;
  const created = result.saved_at || new Date().toISOString();
  return {
    id: result.trip_id || localId,
    created_at: created,
    current_location: inputs.current_location || "",
    pickup_location: inputs.pickup_location || "",
    dropoff_location: inputs.dropoff_location || "",
    current_cycle_used_hours: inputs.current_cycle_used_hours,
    driver_name: header.driver_name || "",
    carrier_name: header.carrier_name || "",
    total_miles: summary.total_miles,
    total_drive_hours: summary.total_drive_hours,
    num_days: summary.num_days,
    result,
  };
}

export function loadHistory() {
  const items = loadJson(HISTORY_KEY, []);
  const active = loadJson(ACTIVE_KEY, null);
  if (!active) return items;
  const activeId = active.trip_id || active.local_id;
  if (activeId && items.some((item) => String(item.id) === String(activeId))) {
    return items;
  }
  return [toHistoryEntry(active), ...items].slice(0, HISTORY_LIMIT);
}

function rememberTrip(result) {
  if (!result) return result;
  const localId = result.local_id || result.trip_id || `local-${Date.now()}`;
  const stored = {
    ...result,
    local_id: localId,
    saved_at: result.saved_at || new Date().toISOString(),
  };
  const entry = toHistoryEntry(stored);
  const next = [entry, ...loadHistory().filter((item) => String(item.id) !== String(entry.id))]
    .slice(0, HISTORY_LIMIT);
  if (!writeJson(HISTORY_KEY, next)) {
    const slim = next.map((item, index) => (index === 0 ? item : { ...item, result: undefined }));
    writeJson(HISTORY_KEY, slim);
  }
  return stored;
}

export function TripProvider({ children }) {
  const [trip, setTripState] = useState(() => loadJson(ACTIVE_KEY, null));
  const [history, setHistory] = useState(loadHistory);

  const setTrip = (result) => {
    const stored = result ? rememberTrip(result) : null;
    setTripState(stored);
    setHistory(loadHistory());
    try {
      if (stored) localStorage.setItem(ACTIVE_KEY, JSON.stringify(stored));
      else localStorage.removeItem(ACTIVE_KEY);
    } catch {
      /* ignore quota errors */
    }
  };

  return (
    <TripContext.Provider value={{ trip, setTrip, history }}>
      {children}
    </TripContext.Provider>
  );
}

export function useTrip() {
  return useContext(TripContext);
}
