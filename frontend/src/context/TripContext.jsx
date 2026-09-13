import React, { createContext, useContext, useState } from "react";

const TripContext = createContext(null);
const ACTIVE_KEY = "trippilot.activeTrip";
const HISTORY_KEY = "trippilot.tripHistory";
const HISTORY_LIMIT = 50;

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

function newLocalId() {
  return `local-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function slimResult(result) {
  if (!result) return result;
  const route = result.route
    ? { ...result.route, geometry: [] }
    : result.route;
  return { ...result, route, charts: undefined };
}

function toHistoryEntry(result) {
  const inputs = result.inputs || {};
  const summary = result.summary || {};
  const header = inputs.log_header || {};
  const localId = result.local_id || newLocalId();
  const created = result.saved_at || new Date().toISOString();
  return {
    id: localId,
    server_id: result.trip_id || result.server_id || null,
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
    result: slimResult({ ...result, local_id: localId }),
  };
}

function persistHistory(entries) {
  let next = entries.slice(0, HISTORY_LIMIT);
  for (let attempt = 0; attempt < 10; attempt += 1) {
    if (writeJson(HISTORY_KEY, next)) return next;
    next = next.map((item, index) => (
      index === 0 ? item : { ...item, result: undefined }
    ));
    if (attempt >= 3) next = next.slice(0, Math.max(1, next.length - 1));
  }
  return next;
}

function normalizeEntry(item) {
  if (!item || !item.id) return null;
  if (String(item.id).startsWith("local-")) return item;
  return {
    ...item,
    server_id: item.server_id || item.id,
    id: `local-migrated-${item.id}-${item.created_at || newLocalId()}`,
  };
}

export function loadHistory() {
  const items = (loadJson(HISTORY_KEY, []) || []).map(normalizeEntry).filter(Boolean);
  const active = loadJson(ACTIVE_KEY, null);
  if (!active) return items;
  const activeId = active.local_id;
  if (activeId && items.some((item) => String(item.id) === String(activeId))) {
    return items;
  }
  return persistHistory([toHistoryEntry(active), ...items]);
}

function rememberTrip(result) {
  if (!result) return result;
  const isNewPlan = !result.local_id;
  const localId = result.local_id || newLocalId();
  const stored = {
    ...result,
    local_id: localId,
    saved_at: isNewPlan ? new Date().toISOString() : (result.saved_at || new Date().toISOString()),
  };
  const entry = toHistoryEntry(stored);
  const existing = loadHistory();
  const next = isNewPlan
    ? [entry, ...existing]
    : [entry, ...existing.filter((item) => String(item.id) !== String(localId))];
  persistHistory(next);
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
      writeJson(ACTIVE_KEY, slimResult(stored));
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
