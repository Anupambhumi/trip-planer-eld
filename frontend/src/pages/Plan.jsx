import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { planTrip } from "../apiClient";
import { useTrip } from "../context/TripContext";
import CityAutocomplete from "../components/CityAutocomplete";
import {
  IconPin, IconNav, IconFlag, IconGauge, IconCheck, IconChevron, IconChevronLeft,
} from "../components/Icons";

const STEPS = [
  { key: "current_location", title: "Current Location", icon: IconPin,
    desc: "Enter the current location for your trip.", label: "Current Location", placeholder: "Start typing a city…" },
  { key: "pickup_location", title: "Pickup Location", icon: IconNav,
    desc: "Where will you pick up the load?", label: "Pickup Location", placeholder: "Pickup city…" },
  { key: "dropoff_location", title: "Dropoff Location", icon: IconFlag,
    desc: "Where is the load headed?", label: "Dropoff Location", placeholder: "Dropoff city…" },
  { key: "current_cycle_used_hours", title: "Cycle Hours Used", icon: IconGauge,
    desc: "On-duty hours already used in the 70hr / 8day cycle.", label: "Cycle Hours Used", placeholder: "0 – 70", number: true },
  { key: "review", title: "Review & Generate", icon: IconCheck, desc: "" },
];

const EXAMPLE = {
  current_location: "New York", pickup_location: "Dallas",
  dropoff_location: "Denver", current_cycle_used_hours: "10",
};

export default function Plan() {
  const [step, setStep] = useState(0);
  const [form, setForm] = useState({
    current_location: "", pickup_location: "", dropoff_location: "",
    current_cycle_used_hours: "",
  });
  const [header, setHeader] = useState({
    driver_name: "", co_driver_name: "", carrier_name: "",
    main_office_address: "", truck_number: "", trailer_number: "",
  });
  const [showHeader, setShowHeader] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const { setTrip } = useTrip();
  const nav = useNavigate();

  const cur = STEPS[step];
  const setField = (k, v) => setForm({ ...form, [k]: v });
  const setHead = (k, v) => setHeader({ ...header, [k]: v });
  const canContinue = cur.key === "review" || String(form[cur.key] || "").trim();

  const generate = async () => {
    setLoading(true); setError("");
    try {
      const result = await planTrip({
        ...form,
        current_cycle_used_hours: parseFloat(form.current_cycle_used_hours || 0),
        log_header: header,
      });
      setTrip(result);
      nav("/route");
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  return (
    <div className="page">
      <h1 className="page-title">Trip Planner</h1>
      <p className="page-sub">Configure your route and generate FMCSA-compliant ELD logs.</p>

      <div className="stepper">
        {STEPS.map((st, i) => {
          const Icon = st.icon;
          const cls = i === step ? "active" : i < step ? "done" : "";
          return (
            <React.Fragment key={st.key}>
              <div className={"step " + cls} onClick={() => i < step && setStep(i)}
                style={{ cursor: i < step ? "pointer" : "default" }}>
                <div className="step-ico"><Icon size={24} /></div>
                <div className="step-label">{st.title}</div>
              </div>
              {i < STEPS.length - 1 && <div className="step-line" />}
            </React.Fragment>
          );
        })}
      </div>

      <div className="card wizard-card">
        <h2 style={{ fontSize: 28, fontWeight: 800, margin: "0 0 8px" }}>{cur.title}</h2>
        {cur.desc && <p style={{ color: "var(--muted)", fontSize: 16, marginTop: 0 }}>{cur.desc}</p>}

        {cur.key !== "review" ? (
          <div className="field" style={{ marginTop: 20 }}>
            <label>{cur.label}</label>
            {cur.number ? (
              <div className="input-wrap">
                <input
                  className="input plain"
                  type="number" min={0} max={70} step={0.5}
                  value={form[cur.key]}
                  placeholder={cur.placeholder}
                  onChange={(e) => setField(cur.key, e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && canContinue && setStep(step + 1)}
                  autoFocus
                />
              </div>
            ) : (
              <CityAutocomplete
                value={form[cur.key]}
                onChange={(v) => setField(cur.key, v)}
                onEnter={() => canContinue && setStep(step + 1)}
                placeholder={cur.placeholder}
                autoFocus
              />
            )}
          </div>
        ) : (
          <div style={{ marginTop: 16 }}>
            <Review k="Current" v={form.current_location} />
            <Review k="Pickup" v={form.pickup_location} />
            <Review k="Dropoff" v={form.dropoff_location} />
            <Review k="Cycle used" v={`${form.current_cycle_used_hours || 0}h`} />

            <div className="collapse" onClick={() => setShowHeader(!showHeader)}>
              {showHeader ? "▼" : "▶"} Optional log header info
            </div>
            {showHeader && (
              <div className="form-2" style={{ marginTop: 16 }}>
                <HField label="Driver Name" k="driver_name" v={header} set={setHead} />
                <HField label="Co-Driver Name" k="co_driver_name" v={header} set={setHead} />
                <HField label="Carrier Name" k="carrier_name" v={header} set={setHead} />
                <HField label="Main Office Address" k="main_office_address" v={header} set={setHead} />
                <HField label="Truck Number" k="truck_number" v={header} set={setHead} />
                <HField label="Trailer Number" k="trailer_number" v={header} set={setHead} />
              </div>
            )}
          </div>
        )}

        {error && <div className="error">{error}</div>}

        <div className="wizard-foot">
          <button className="btn btn-ghost"
            onClick={() => (step === 0 ? setForm(EXAMPLE) : setStep(step - 1))}>
            {step === 0 ? "Use example" : <><IconChevronLeft size={16} /> Back</>}
          </button>
          {cur.key === "review" ? (
            <button className="btn" onClick={generate} disabled={loading}>
              {loading ? <><span className="spinner" /> Generating…</> : "Generate Route & Logs"}
            </button>
          ) : (
            <button className="btn" disabled={!canContinue} onClick={() => setStep(step + 1)}>
              Continue <IconChevron size={16} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

const Review = ({ k, v }) => (
  <div className="review-row"><span className="k">{k}</span><span className="v">{v || "—"}</span></div>
);

const HField = ({ label, k, v, set }) => (
  <div className="field">
    <label>{label}</label>
    <input className="input plain" value={v[k]} onChange={(e) => set(k, e.target.value)} />
  </div>
);
