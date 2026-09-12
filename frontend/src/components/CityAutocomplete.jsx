import React, { useEffect, useRef, useState } from "react";
import { suggestCities } from "../apiClient";
import { IconPin } from "./Icons";

/**
 * Debounced US-city autocomplete. Free text is still allowed — suggestions
 * just help. Keyboard: ↑/↓ to move, Enter to pick, Esc to close.
 */
export default function CityAutocomplete({
  value, onChange, onEnter, placeholder, autoFocus,
}) {
  const [items, setItems] = useState([]);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const [loading, setLoading] = useState(false);
  const boxRef = useRef(null);
  const abortRef = useRef(null);
  const justPicked = useRef(false);

  // Debounced fetch as the user types.
  useEffect(() => {
    if (justPicked.current) { justPicked.current = false; return; }
    const q = (value || "").trim();
    if (q.length < 2) { setItems([]); setOpen(false); return; }
    setLoading(true);
    const t = setTimeout(async () => {
      if (abortRef.current) abortRef.current.abort();
      const ctrl = new AbortController();
      abortRef.current = ctrl;
      try {
        const data = await suggestCities(q, ctrl.signal);
        setItems(data);
        setOpen(data.length > 0);
        setActive(-1);
      } catch { /* aborted / offline */ }
      finally { setLoading(false); }
    }, 300);
    return () => clearTimeout(t);
  }, [value]);

  // Close on outside click.
  useEffect(() => {
    const h = (e) => { if (boxRef.current && !boxRef.current.contains(e.target)) setOpen(false); };
    document.addEventListener("mousedown", h);
    return () => document.removeEventListener("mousedown", h);
  }, []);

  const pick = (item) => {
    justPicked.current = true;
    onChange(item.label);
    setOpen(false);
    setItems([]);
    setActive(-1);
  };

  const onKeyDown = (e) => {
    if (open && items.length) {
      if (e.key === "ArrowDown") { e.preventDefault(); setActive((a) => (a + 1) % items.length); return; }
      if (e.key === "ArrowUp") { e.preventDefault(); setActive((a) => (a - 1 + items.length) % items.length); return; }
      if (e.key === "Enter" && active >= 0) { e.preventDefault(); pick(items[active]); return; }
      if (e.key === "Escape") { setOpen(false); return; }
    }
    if (e.key === "Enter" && onEnter) onEnter();
  };

  return (
    <div className="ac-wrap" ref={boxRef}>
      <div className="input-wrap">
        <span className="lead"><IconPin size={18} /></span>
        <input
          className="input"
          value={value}
          placeholder={placeholder}
          autoFocus={autoFocus}
          autoComplete="off"
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => items.length && setOpen(true)}
          onKeyDown={onKeyDown}
        />
        {loading && <span className="ac-spin" />}
      </div>
      {open && items.length > 0 && (
        <ul className="ac-menu">
          {items.map((it, i) => (
            <li
              key={it.label}
              className={"ac-item" + (i === active ? " active" : "")}
              onMouseEnter={() => setActive(i)}
              onMouseDown={(e) => { e.preventDefault(); pick(it); }}
            >
              <IconPin size={15} className="ac-ico" />
              {it.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
