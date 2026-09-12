import React from "react";
import { MapContainer, TileLayer, Polyline, CircleMarker, Tooltip } from "react-leaflet";

const COLORS = {
  start: "#38bdf8", pickup: "#22d3ee", dropoff: "#f2555a",
  fuel: "#f5a524", rest: "#6366f1", restart: "#a78bfa",
  break: "#2dd4bf", stop: "#8aa0c0",
};
const LABELS = {
  start: "Start", pickup: "Pickup", dropoff: "Drop-off", fuel: "Fuel",
  rest: "10h rest", restart: "34h restart", break: "30m break", stop: "Stop",
};

export default function RouteMap({ route, stops, height = 460 }) {
  const line = route.geometry || [];
  const center = line[Math.floor(line.length / 2)] || [39.5, -98.35];
  const bounds = line.length
    ? line.reduce(
        (b, p) => [
          [Math.min(b[0][0], p[0]), Math.min(b[0][1], p[1])],
          [Math.max(b[1][0], p[0]), Math.max(b[1][1], p[1])],
        ],
        [[line[0][0], line[0][1]], [line[0][0], line[0][1]]]
      )
    : null;

  const big = new Set(["start", "pickup", "dropoff"]);
  const present = [...new Set(stops.map((s) => s.type))];

  return (
    <>
      <div className="map-box">
        <MapContainer center={center} bounds={bounds} scrollWheelZoom
          style={{ height }}>
          <TileLayer
            attribution='&copy; OpenStreetMap'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <Polyline positions={line} pathOptions={{ color: "#38bdf8", weight: 4 }} />
          {stops.filter((s) => s.lat != null).map((s, i) => (
            <CircleMarker key={i} center={[s.lat, s.lon]}
              radius={big.has(s.type) ? 9 : 6}
              pathOptions={{ color: "#070d1c", weight: 2,
                fillColor: COLORS[s.type] || "#8aa0c0", fillOpacity: 1 }}>
              <Tooltip>
                <b>{s.label}</b><br />
                {s.mile != null && <>Mile {s.mile} · </>}{s.arrive_time}
              </Tooltip>
            </CircleMarker>
          ))}
        </MapContainer>
      </div>
      <div className="legend">
        {present.map((k) => (
          <div className="item" key={k}>
            <span className="dot" style={{ background: COLORS[k] }} />
            {LABELS[k] || k}
          </div>
        ))}
      </div>
    </>
  );
}
