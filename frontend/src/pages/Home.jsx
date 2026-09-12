import React from "react";
import { Link } from "react-router-dom";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  RadialBarChart, RadialBar, AreaChart, Area, Legend,
  BarChart, Bar,
} from "recharts";
import { useTrip } from "../context/TripContext";
import {
  IconRoute, IconClock, IconFuel, IconGauge, IconCalendar, IconFile, IconArrow,
} from "../components/Icons";

const TEAL = "#0d9488";
const EMERALD = "#059669";
const CORAL = "#ea580c";
const SLATE = "#64748b";

const axis = { stroke: "#64748b", fontSize: 12, tickLine: false };
const tooltipStyle = {
  background: "rgba(255, 255, 255, 0.82)", border: "1px solid rgba(255,255,255,0.55)",
  borderRadius: 12, color: "#122033", backdropFilter: "blur(14px)",
  boxShadow: "0 16px 40px -12px rgba(15,40,80,0.25)",
};

function Stat({ icon: Icon, k, v, tone }) {
  return (
    <div className="stat">
      <div className={"stat-ico" + (tone ? " " + tone : "")}><Icon /></div>
      <div className="stat-k">{k}</div>
      <div className="stat-v">{v}</div>
    </div>
  );
}

export default function Home() {
  const { trip } = useTrip();
  const s = trip?.summary;
  const c = trip?.charts;

  return (
    <div className="page">
      <section className="hero">
        <div className="hero-copy">
          <span className="chip"><span className="dot" /> TripPilot AI • FMCSA 70hr/8day</span>
          <h1>HOS Route Intelligence Platform</h1>
          <p>Plan FMCSA-compliant routes, generate ELD logs, and optimize long-haul operations.</p>
          <div className="hero-cta">
            <Link to="/plan" className="btn">Plan New Trip <IconArrow size={18} /></Link>
            <Link to="/logs" className="btn btn-outline">View ELD Logs</Link>
          </div>
        </div>
        <div className="hero-art">
          <VehicleArt />
        </div>
      </section>

      {!trip ? (
        <div className="card empty" style={{ marginTop: 30 }}>
          <h3>No active trip</h3>
          <p>Plan a new trip or open an existing one from your trip history.</p>
          <div className="hero-cta center" style={{ justifyContent: "center", marginTop: 18 }}>
            <Link to="/plan" className="btn">Plan Your First Trip</Link>
            <Link to="/trips" className="btn btn-outline">View All Trips</Link>
          </div>
        </div>
      ) : (
        <>
          <div className="grid stat-grid" style={{ marginTop: 26 }}>
            <Stat icon={IconRoute} k="Total Distance" v={`${s.total_miles.toLocaleString()} mi`} />
            <Stat icon={IconClock} k="Driving Time" v={`${s.total_drive_hours}h`} />
            <Stat icon={IconFuel} k="Fuel Stops" v={s.fuel_stops} tone="amber" />
            <Stat icon={IconGauge} k="Cycle Remaining" v={`${trip.hos.cycle_remaining}h`} tone="red" />
            <Stat icon={IconCalendar} k="Trip Days" v={s.num_days} />
            <Stat icon={IconFile} k="Log Sheets" v={s.num_days} />
          </div>

          <div className="grid chart-2" style={{ marginTop: 22 }}>
            <div className="card">
              <h2 className="card-h">Driving Hours by Day</h2>
              <div className="chart-box">
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={c.driving_by_day} margin={{ left: -18, right: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(13,148,136,0.12)" />
                    <XAxis dataKey="date" {...axis} tickFormatter={(d) => d.slice(5)} />
                    <YAxis {...axis} />
                    <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "rgba(13,148,136,0.06)" }} />
                    <Bar dataKey="hours" fill={TEAL} radius={[8, 8, 0, 0]} maxBarSize={42} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="card">
              <h2 className="card-h">Duty Status Breakdown</h2>
              <div className="chart-box center">
                <ResponsiveContainer width="100%" height={280}>
                  <RadarChart data={[
                    { name: "Driving", hours: c.duty_breakdown.driving },
                    { name: "On Duty", hours: c.duty_breakdown.on_duty },
                    { name: "Off Duty", hours: c.duty_breakdown.off_duty },
                  ]}>
                    <PolarGrid stroke="rgba(13,148,136,0.2)" />
                    <PolarAngleAxis dataKey="name" tick={{ fill: "#4d6480", fontSize: 12 }} />
                    <PolarRadiusAxis tick={{ fill: SLATE, fontSize: 10 }} />
                    <Radar dataKey="hours" stroke={EMERALD} fill={EMERALD} fillOpacity={0.35} />
                    <Tooltip contentStyle={tooltipStyle} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          <div className="grid chart-2" style={{ marginTop: 22 }}>
            <div className="card">
              <h2 className="card-h">Cycle Usage (70h)</h2>
              <div className="chart-box center">
                <ResponsiveContainer width="100%" height={280}>
                  <RadialBarChart
                    innerRadius="55%" outerRadius="95%"
                    data={[
                      { name: "Used", value: c.cycle_usage.used, fill: TEAL },
                      { name: "Remaining", value: c.cycle_usage.remaining, fill: "rgba(13,148,136,0.15)" },
                    ]}
                    startAngle={90} endAngle={-270}>
                    <RadialBar dataKey="value" cornerRadius={8} background />
                    <Legend iconType="circle" formatter={(v) => <span style={{ color: "#4d6480" }}>{v}</span>} />
                    <Tooltip contentStyle={tooltipStyle} />
                  </RadialBarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="card">
              <h2 className="card-h">Trip Progress</h2>
              <div className="chart-box">
                <ResponsiveContainer width="100%" height={280}>
                  <AreaChart data={c.trip_progress} margin={{ left: -18 }}>
                    <defs>
                      <linearGradient id="tp" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={CORAL} stopOpacity={0.45} />
                        <stop offset="100%" stopColor={CORAL} stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(234,88,12,0.12)" />
                    <XAxis dataKey="date" {...axis} tickFormatter={(d) => d.slice(5)} />
                    <YAxis {...axis} />
                    <Tooltip contentStyle={tooltipStyle} />
                    <Area type="monotone" dataKey="miles" stroke={CORAL} fill="url(#tp)" strokeWidth={2.5} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {c.fuel_stops.length > 0 && (
            <div className="card" style={{ marginTop: 22 }}>
              <h2 className="card-h">Fuel Stops</h2>
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={c.fuel_stops} margin={{ left: -10, right: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(234,88,12,0.12)" />
                  <XAxis dataKey="label" {...axis} />
                  <YAxis {...axis} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Line type="monotone" dataKey="mile" stroke={CORAL} strokeWidth={3}
                    dot={{ r: 5, fill: CORAL, stroke: "#fff", strokeWidth: 2 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function Wheel({ cx, cy, r = 16 }) {
  return (
    <g className="tp-wheel">
      <circle cx={cx} cy={cy} r={r} fill="#1e293b" stroke="#0f172a" strokeWidth="3" />
      <circle cx={cx} cy={cy} r={r - 4} fill="none" stroke="#475569" strokeWidth="2" />
      <circle cx={cx} cy={cy} r={r - 8} fill="#334155" />
      {[0, 72, 144, 216, 288].map((a) => (
        <path key={a} d={`M${cx} ${cy} L${cx - 2.4} ${cy - (r - 7)} h4.8 z`}
          fill="#fbbf24" opacity="0.9"
          transform={`rotate(${a} ${cx} ${cy})`} />
      ))}
      <circle cx={cx} cy={cy} r="3.2" fill="#fde68a" />
    </g>
  );
}

function City({ dx = 0 }) {
  const bars = [10, 60, 105, 150, 205, 260, 300, 350, 400];
  return (
    <g transform={`translate(${dx} 0)`}>
      {bars.map((x, i) => (
        <rect key={i} x={x} y={120 - (i % 4) * 16} width="38"
          height={130 + (i % 4) * 16} rx="6" fill="#94a3b8" opacity="0.35" />
      ))}
    </g>
  );
}

function VehicleArt() {
  return (
    <svg className="tp-scene" viewBox="10 120 340 180" role="img"
      aria-label="Animated pickup truck driving along the road"
      preserveAspectRatio="xMidYMid slice">
      <defs>
        <linearGradient id="pickupBody" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#fb923c" />
          <stop offset="55%" stopColor="#ea580c" />
          <stop offset="100%" stopColor="#c2410c" />
        </linearGradient>
        <linearGradient id="pickupGlass" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#e0f2fe" />
          <stop offset="100%" stopColor="#7dd3fc" />
        </linearGradient>
        <radialGradient id="under" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.7" />
          <stop offset="100%" stopColor="#f59e0b" stopOpacity="0" />
        </radialGradient>
        <filter id="soft"><feGaussianBlur stdDeviation="6" /></filter>
        <clipPath id="scene"><rect x="0" y="0" width="460" height="300" /></clipPath>
      </defs>

      <g clipPath="url(#scene)">
        <g className="tp-city"><City dx={-460} /><City dx={0} /></g>

        <rect x="0" y="252" width="460" height="48" fill="#94a3b8" />
        <rect x="0" y="251" width="460" height="2" fill="#64748b" opacity="0.7" />

        <g className="tp-road">
          {Array.from({ length: 16 }).map((_, i) => (
            <rect key={i} x={-40 + i * 40} y="286" width="22" height="4" rx="2"
              fill="#f8fafc" />
          ))}
        </g>

        <g>
          {[208, 220, 232].map((y, i) => (
            <rect key={y} className="tp-streak" x="250" y={y} width="54" height="3"
              rx="1.5" fill="#fb923c" style={{ animationDelay: `${i * 0.35}s` }} />
          ))}
        </g>

        <ellipse className="tp-glow" cx="150" cy="258" rx="120" ry="16"
          fill="url(#under)" filter="url(#soft)" />

        {/* Pickup sits lower-left and faces left */}
        <g className="tp-truck" transform="translate(8 10)">
          <path d="M52 238 H268 q8 0 8-8 V200 q0-8-8-8 H150 V176 q0-10-10-12 H78 q-14 0-22 12 L46 196 q-6 6-6 14 v20 q0 8 12 8 z"
            fill="url(#pickupBody)" />
          <path d="M78 178 q-8 0-12 10 L56 204 h62 V180 q0-2-2-2 H78 z"
            fill="url(#pickupGlass)" />
          <rect x="156" y="178" width="104" height="12" rx="2" fill="#9a3412" />
          <rect x="164" y="158" width="26" height="20" rx="3" fill="#fde68a" />
          <rect x="196" y="150" width="28" height="28" rx="3" fill="#fbbf24" />
          <rect x="230" y="160" width="22" height="18" rx="3" fill="#fdba74" />
          <rect x="52" y="226" width="216" height="10" rx="3" fill="#7c2d12" />
          <rect className="tp-lightbar" x="258" y="204" width="8" height="14" rx="2" fill="#fef3c7" />
          <rect className="tp-headlight" x="40" y="212" width="12" height="14" rx="3" fill="#fefce8" />
          <path className="tp-headlight" d="M40 212 l-26 -8 v30 l26 -6 z" fill="#fde68a" opacity="0.4" />

          <Wheel cx="92" cy="242" />
          <Wheel cx="222" cy="242" />
        </g>
      </g>
    </svg>
  );
}
