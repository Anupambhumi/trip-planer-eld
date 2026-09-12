import React from "react";
import { Routes, Route, useLocation } from "react-router-dom";
import Navbar from "./components/Navbar";
import Home from "./pages/Home";
import Trips from "./pages/Trips";
import Plan from "./pages/Plan";
import RouteAnalysis from "./pages/RouteAnalysis";
import HoursOfService from "./pages/HoursOfService";
import Logs from "./pages/Logs";

export default function App() {
  const location = useLocation();
  return (
    <>
      {/* Drifting color orbs behind the glass panels. */}
      <div className="aurora" aria-hidden="true"><span /><span /><span /><span /></div>
      <Navbar />
      <div className="shell">
        {/* Keyed by path so every page plays its entrance animation. */}
        <div className="route-view" key={location.pathname}>
          <Routes location={location}>
            <Route path="/" element={<Home />} />
            <Route path="/trips" element={<Trips />} />
            <Route path="/plan" element={<Plan />} />
            <Route path="/route" element={<RouteAnalysis />} />
            <Route path="/hos" element={<HoursOfService />} />
            <Route path="/logs" element={<Logs />} />
          </Routes>
        </div>
      </div>
    </>
  );
}
