import "./ToggleTabs.css";

export default function ToggleTabs({ active, onChange }) {
  return (
    <div className="toggle-tabs" role="tablist" aria-label="Billing period">
      <button
        role="tab"
        aria-selected={active === "month"}
        className={`tab ${active === "month" ? "active" : ""}`}
        onClick={() => onChange("month")}
      >
        Monthly
      </button>
      <button
        role="tab"
        aria-selected={active === "year"}
        className={`tab ${active === "year" ? "active" : ""}`}
        onClick={() => onChange("year")}
      >
        Yearly
      </button>
    </div>
  );
}
