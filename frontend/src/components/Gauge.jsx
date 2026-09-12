import React from "react";

export default function Gauge({ value, max, color = "#38bdf8", label, desc, unit }) {
  const r = 62;
  const c = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(1, max ? value / max : 0));
  const dash = c * pct;
  return (
    <div className="gauge-card card">
      <div className="gauge-ring">
        <svg width="150" height="150" viewBox="0 0 150 150">
          <circle cx="75" cy="75" r={r} fill="none"
            stroke="rgba(56,189,248,0.12)" strokeWidth="10" />
          <circle className="gauge-arc" cx="75" cy="75" r={r} fill="none" stroke={color}
            strokeWidth="10" strokeLinecap="round"
            strokeDasharray={`${dash} ${c}`}
            transform="rotate(-90 75 75)"
            style={{ filter: `drop-shadow(0 0 6px ${color}66)` }} />
        </svg>
        <div className="gauge-num">
          <b>{value.toFixed(1)}</b>
          <span>/ {max}{unit || "h"}</span>
        </div>
      </div>
      <div className="gauge-title">{label}</div>
      <div className="gauge-desc">{desc}</div>
    </div>
  );
}
