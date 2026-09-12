import React, { createContext, useContext, useState } from "react";

const TripContext = createContext(null);
const KEY = "trippilot.activeTrip";

function load() {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function TripProvider({ children }) {
  const [trip, setTripState] = useState(load);

  const setTrip = (result) => {
    setTripState(result);
    try {
      if (result) localStorage.setItem(KEY, JSON.stringify(result));
      else localStorage.removeItem(KEY);
    } catch {
      /* ignore quota errors */
    }
  };

  return (
    <TripContext.Provider value={{ trip, setTrip }}>
      {children}
    </TripContext.Provider>
  );
}

export function useTrip() {
  return useContext(TripContext);
}
