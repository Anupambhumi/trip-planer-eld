import React from "react";
import { NavLink } from "react-router-dom";
import { useTrip } from "../context/TripContext";
import {
  IconHome, IconTrips, IconPlan, IconMap, IconClock, IconFile,
} from "./Icons";

const LINKS = [
  { to: "/", label: "Home", icon: IconHome, end: true },
  { to: "/trips", label: "Trips", icon: IconTrips },
  { to: "/plan", label: "Plan", icon: IconPlan },
  { to: "/route", label: "Route", icon: IconMap },
  { to: "/hos", label: "HOS", icon: IconClock },
  { to: "/logs", label: "Logs", icon: IconFile },
];

function BrandLogo() {
  return (
    <span className="brand-mark" aria-hidden="true">
      <svg viewBox="0 0 24 24" fill="none">
        <path d="M3 15.5h11.5V9.2H8.2L6.4 6.5H3v9z" fill="#fff" opacity="0.95" />
        <path d="M14.5 11.2h3.2l2.3 2.6V15.5H14.5V11.2z" fill="#ccfbf1" />
        <circle cx="7.2" cy="16.6" r="1.55" fill="#fde68a" stroke="#fff" strokeWidth="0.8" />
        <circle cx="17.2" cy="16.6" r="1.55" fill="#fde68a" stroke="#fff" strokeWidth="0.8" />
        <path d="M3.2 18.8h17.6" stroke="#fff" strokeWidth="1.4" strokeLinecap="round" opacity="0.55" />
      </svg>
    </span>
  );
}

function initials(trip) {
  const name = trip?.inputs?.log_header?.driver_name;
  if (name) {
    return name.trim().split(/\s+/).map((w) => w[0]).join("").slice(0, 2).toUpperCase();
  }
  return "TP";
}

export default function Navbar() {
  const { trip } = useTrip();
  return (
    <nav className="nav">
      <div className="nav-inner">
        <div className="brand">
          <BrandLogo />
          TripPilot <span style={{ color: "var(--mint)", marginLeft: 4 }}>AI</span>
        </div>
        <div className="nav-pills">
          {LINKS.map(({ to, label, icon: Icon, end }) => (
            <NavLink key={to} to={to} end={end}
              className={({ isActive }) => "nav-pill" + (isActive ? " active" : "")}>
              <Icon /><span>{label}</span>
            </NavLink>
          ))}
        </div>
        <div className="avatar">{initials(trip)}</div>
      </div>
    </nav>
  );
}
