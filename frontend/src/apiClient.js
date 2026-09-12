const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function parseJsonOrThrow(response) {
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Request failed.");
  return data;
}

export async function planTrip(payload) {
  const response = await fetch(`${API_BASE_URL}/api/plan/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseJsonOrThrow(response);
}

export async function listTrips() {
  const response = await fetch(`${API_BASE_URL}/api/trips/`);
  return parseJsonOrThrow(response);
}

export async function getTrip(tripId) {
  const response = await fetch(`${API_BASE_URL}/api/trips/${tripId}/`);
  return parseJsonOrThrow(response);
}

export async function suggestCities(query, signal) {
  const response = await fetch(
    `${API_BASE_URL}/api/geocode/suggest/?q=${encodeURIComponent(query)}`, { signal });
  if (!response.ok) return [];
  return response.json();
}
