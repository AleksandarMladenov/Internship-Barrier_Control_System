import React from "react";
import "./Subscription.css";

function money(cents, currency = "EUR") {
  const n = Number(cents || 0) / 100;
  try {
    return new Intl.NumberFormat(undefined, { style: "currency", currency }).format(n);
  } catch {
    return `${n.toFixed(2)} ${currency}`;
  }
}

// --- helpers
const norm = (v) => (v ?? "").toString().trim().toLowerCase();
const isMonth = (v) => ["m", "mon", "month", "monthly"].includes(norm(v));
const isYear  = (v) => ["y", "yr", "year", "yearly", "annual", "annually"].includes(norm(v));

export default function PlanSelector({
  plans,
  period,
  onPeriodChange,
  selectedPlanId,
  onSelectPlan,
}) {
  const filtered = plans.filter(p =>
    period === "month" ? isMonth(p.billing_period) : isYear(p.billing_period)
  );

  return (
    <>
      <div className="header">
        <h2>Choose a plan</h2>
        <span className="subtle">Select billing period, then pick a plan</span>
      </div>

      <div className="toggle-row" role="tablist" aria-label="Billing period">
        <button
          className={`toggle ${period === "month" ? "active" : ""}`}
          onClick={() => onPeriodChange("month")}
          role="tab"
          aria-selected={period === "month"}
        >
          Monthly
        </button>
        <button
          className={`toggle ${period === "year" ? "active" : ""}`}
          onClick={() => onPeriodChange("year")}
          role="tab"
          aria-selected={period === "year"}
        >
          Yearly
        </button>
      </div>

      <div className="grid" role="list">
        {filtered.map((plan) => (
          <article
            key={plan.id}
            className={`plan-card ${selectedPlanId === plan.id ? "selected" : ""}`}
            onClick={() => onSelectPlan(plan.id)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && onSelectPlan(plan.id)}
            aria-pressed={selectedPlanId === plan.id}
          >
            <h3 className="plan-title">{plan.name || "Basic"}</h3>
            <p className="plan-price">
              {money(plan.period_price_cents, plan.currency)}
              <span className="subtle"> / {plan.billing_period}</span>
            </p>
            <ul className="benefits">
              <li>🚘 1 vehicle</li>
              <li>✅ Cancel anytime</li>
            </ul>
            {selectedPlanId === plan.id && <div className="checkmark">✓ Selected</div>}
          </article>
        ))}

        {!filtered.length && (
          <div className="empty">
            No plans for <strong>{period}</strong> yet.
          </div>
        )}
      </div>
    </>
  );
}
