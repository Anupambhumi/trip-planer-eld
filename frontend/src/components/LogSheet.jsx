import React from "react";

const ROWS = [
  { key: "OFF", label: "1. Off Duty" },
  { key: "SB", label: "2. Sleeper Berth" },
  { key: "D", label: "3. Driving" },
  { key: "ON", label: "4. On Duty (not driving)" },
];
const ROW_INDEX = { OFF: 0, SB: 1, D: 2, ON: 3 };

const LABEL_W = 168;
const HOUR_W = 34;
const GRID_W = HOUR_W * 24;
const TOTAL_W = 74;
const HEAD_H = 96;
const HOURHDR_H = 22;
const ROW_H = 36;
const GRID_H = ROW_H * 4;
const REMARK_H = 132;
const W = LABEL_W + GRID_W + TOTAL_W;
const H = HEAD_H + HOURHDR_H + GRID_H + REMARK_H;
const GRID_TOP = HEAD_H + HOURHDR_H;

const xAt = (min) => LABEL_W + (min / 1440) * GRID_W;
const rowCenter = (k) => GRID_TOP + ROW_INDEX[k] * ROW_H + ROW_H / 2;
const hourLabel = (h) => (h === 0 || h === 24 ? "M" : h === 12 ? "N" : h > 12 ? h - 12 : h);

export default function LogSheet({ log, scale = 1 }) {
  const totals = log.totals_hours;
  const header = log.header || {};

  const path = [];
  log.segments.forEach((s, i) => {
    const y = rowCenter(s.status);
    const x1 = xAt(s.start);
    const x2 = xAt(s.end);
    if (i === 0) path.push(`M ${x1} ${y}`);
    else path.push(`L ${x1} ${y}`);
    path.push(`L ${x2} ${y}`);
  });

  const field = (x, y, k, v) => (
    <>
      <text x={x} y={y} fontSize="10" fill="#64748b" fontWeight="600"
        letterSpacing="0.04em">{k}</text>
      <text x={x} y={y + 18} fontSize="14" fill="#0f172a" fontWeight="700">
        {v || "—"}</text>
    </>
  );

  return (
    <div style={{ width: `${scale * 100}%`, minWidth: 720 }}>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" style={{ fontFamily: "Inter, sans-serif" }}>
        <rect x="0" y="0" width={W} height={H} fill="#fff" rx="4" />

        {/* Title */}
        <text x={W / 2} y="30" textAnchor="middle" fontSize="20" fontWeight="800"
          fill="#0f172a" letterSpacing="0.04em">DRIVER'S DAILY LOG</text>
        <text x={W / 2} y="48" textAnchor="middle" fontSize="11" fill="#64748b">
          (ONE CALENDAR DAY — 24 HOURS)</text>

        {/* Header fields */}
        {field(LABEL_W - 150, 74, "Date", log.date)}
        {field(LABEL_W + 30, 74, "Total miles driving today", String(log.total_miles_today ?? 0))}
        {field(LABEL_W + GRID_W - 260, 74, "Vehicle numbers",
          [header.truck_number, header.trailer_number].filter(Boolean).join(" / "))}
        {field(LABEL_W + GRID_W - 60, 74, "Driver", header.driver_name)}

        {/* Hour header */}
        {Array.from({ length: 25 }).map((_, h) => (
          <text key={h} x={xAt(h * 60)} y={HEAD_H + 14} textAnchor="middle"
            fontSize="10" fill="#475569">{hourLabel(h)}</text>
        ))}
        <text x={LABEL_W + GRID_W + TOTAL_W / 2} y={HEAD_H + 14} textAnchor="middle"
          fontSize="10" fill="#475569" fontWeight="700">Total Hrs</text>

        {/* Rows */}
        {ROWS.map((r, ri) => {
          const yTop = GRID_TOP + ri * ROW_H;
          return (
            <g key={r.key}>
              <rect x={LABEL_W} y={yTop} width={GRID_W} height={ROW_H}
                fill={ri % 2 ? "#f8fafc" : "#fff"} stroke="#cbd5e1" />
              <text x={LABEL_W - 10} y={yTop + ROW_H / 2 + 4} textAnchor="end"
                fontSize="12" fill="#0f172a" fontWeight="600">{r.label}</text>
              <rect x={LABEL_W + GRID_W} y={yTop} width={TOTAL_W} height={ROW_H}
                fill="#fff" stroke="#cbd5e1" />
              <text x={LABEL_W + GRID_W + TOTAL_W / 2} y={yTop + ROW_H / 2 + 5}
                textAnchor="middle" fontSize="14" fontWeight="700" fill="#0f172a">
                {totals[r.key].toFixed(2)}</text>
            </g>
          );
        })}

        {/* tick marks: hour + 15-min */}
        {Array.from({ length: 24 * 4 + 1 }).map((_, q) => {
          const x = LABEL_W + (q / 96) * GRID_W;
          const isHour = q % 4 === 0;
          return (
            <line key={q} x1={x} y1={GRID_TOP} x2={x} y2={GRID_TOP + GRID_H}
              stroke={isHour ? "#94a3b8" : "#e2e8f0"} strokeWidth="1" />
          );
        })}

        {/* Duty status line */}
        <path d={path.join(" ")} fill="none" stroke="#1d4ed8" strokeWidth="2.4"
          strokeLinejoin="round" strokeLinecap="round" />

        {/* Remarks */}
        <text x={LABEL_W - 10} y={GRID_TOP + GRID_H + 26} textAnchor="end"
          fontSize="12" fill="#0f172a" fontWeight="600">Remarks</text>
        <rect x={LABEL_W} y={GRID_TOP + GRID_H + 6} width={GRID_W + TOTAL_W}
          height={REMARK_H - 16} fill="#fff" stroke="#cbd5e1" />
        {log.remarks.map((rm, i) => {
          const x = xAt(rm.minute);
          return (
            <g key={i}>
              <line x1={x} y1={GRID_TOP + GRID_H} x2={x} y2={GRID_TOP + GRID_H + 20}
                stroke="#94a3b8" strokeDasharray="2 2" />
              <text x={x + 3} y={GRID_TOP + GRID_H + 34}
                fontSize="10" fill="#334155"
                transform={`rotate(38 ${x + 3} ${GRID_TOP + GRID_H + 34})`}>
                {rm.time} {rm.text}</text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
