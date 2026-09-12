import React from "react";
import { Link } from "react-router-dom";
import { useTrip } from "../context/TripContext";
import RouteMap from "../components/RouteMap";
import Timeline from "../components/Timeline";

export default function RouteAnalysis() {
  const { trip } = useTrip();

  if (!trip) return <EmptyState />;

  return (
    <div className="page">
      <h1 className="page-title">Route Analysis</h1>
      <p className="page-sub">Interactive map and stop-by-stop timeline for the active trip.</p>

      <div style={{ marginBottom: 24 }}>
        <RouteMap route={trip.route} stops={trip.stops} height={480} />
      </div>

      <Timeline items={trip.timeline} title="Route Timeline" />
    </div>
  );
}

function EmptyState() {
  return (
    <div className="page">
      <div className="card empty">
        <h3>No active trip</h3>
        <p>Plan a trip to see its route and timeline.</p>
        <Link to="/plan" className="btn" style={{ marginTop: 14 }}>Plan a Trip</Link>
      </div>
    </div>
  );
}
