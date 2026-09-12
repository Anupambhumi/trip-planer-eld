import React from "react";

function dotClass(item) {
  if (item.status === "D") return "";
  if (item.title.includes("break")) return "rest";
  if (item.title.includes("Fuel")) return "amber";
  return "off";
}

export default function Timeline({ items, title = "Route Timeline" }) {
  return (
    <div className="card">
      <h2 className="card-h">{title}</h2>
      <div className="timeline">
        {items.map((it, i) => (
          <div className="tl-item" key={i}>
            <span className={"tl-dot " + dotClass(it)} />
            <div className="tl-body">
              <div className="tl-head">
                <span className="tl-title">{it.title}</span>
                <span className="tl-dur">{it.duration_str}</span>
              </div>
              <div className="tl-meta">
                {it.start_str} → {it.end_str} · {it.status_label}
                {it.miles ? ` · ${it.miles} mi` : ""}
              </div>
              {it.note && it.note !== it.title && (
                <div className="tl-note">— {it.note}</div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
