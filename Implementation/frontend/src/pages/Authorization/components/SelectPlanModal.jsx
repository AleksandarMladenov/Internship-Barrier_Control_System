import { useEffect, useMemo, useState } from "react";
import { listSubscriptionPlans, createSubscription } from "../../../api/subscriptionsApi";

export default function SelectPlanModal({ vehicle, open = true, onClose, onCreated }) {
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [planId, setPlanId] = useState("");
  const [duration, setDuration] = useState("month"); // week | month | quarter | year | custom
  const [customDays, setCustomDays] = useState(30);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    // load plans whenever the modal is opened
    if (!open) return;
    let ignore = false;
    (async () => {
      setLoading(true);
      setErr("");
      try {
        const data = await listSubscriptionPlans();
        if (!ignore) {
          const items = Array.isArray(data) ? data : (data?.items ?? []);
          setPlans(items);
        }
      } catch (e) {
        if (!ignore) setErr(e?.message || "Failed to load plans");
      } finally {
        if (!ignore) setLoading(false);
      }
    })();
    return () => { ignore = true; };
  }, [open]);

  const nowISO = useMemo(() => new Date().toISOString(), []);
  const endISO = useMemo(() => {
    const start = new Date();
    const d = new Date(start);
    switch (duration) {
      case "week":    d.setDate(d.getDate() + 7); break;
      case "month":   d.setMonth(d.getMonth() + 1); break;
      case "quarter": d.setMonth(d.getMonth() + 3); break;
      case "year":    d.setFullYear(d.getFullYear() + 1); break;
      case "custom":  d.setDate(d.getDate() + Math.max(1, Number(customDays) || 30)); break;
      default:        d.setMonth(d.getMonth() + 1);
    }
    return d.toISOString();
  }, [duration, customDays]);

  async function handleCreate() {
    if (!planId) {
      setErr("Please pick a plan.");
      return;
    }
    setBusy(true);
    setErr("");
    try {
      await createSubscription({
        vehicle_id: vehicle.id,
        plan_id: Number(planId),
        valid_from: nowISO,
        valid_to: endISO,
        auto_renew: true,
      });
      onCreated?.();
      onClose?.();
    } catch (e) {
      setErr(e?.message || "Failed to create subscription");
    } finally {
      setBusy(false);
    }
  }

  // NOTE: no early return on `!open` — parent controls mounting

  return (
    <div className="modal-backdrop">
      <div className="modal">
        <h3>Link Subscription</h3>
        <p>Vehicle: <b>{vehicle.region_code} {vehicle.plate_text}</b></p>

        {loading ? (
          <p>Loading plans…</p>
        ) : err ? (
          <p className="error">{err}</p>
        ) : plans.length === 0 ? (
          <p>No subscription plans configured.</p>
        ) : (
          <>
            <label className="form-row">
              <span>Plan</span>
              <select value={planId} onChange={e => setPlanId(e.target.value)}>
                <option value="" disabled>Pick a plan…</option>
                {plans.map(p => (
                  <option key={p.id} value={p.id}>
                    {p.name} · {p.currency} {(p.price_flat_cents ?? p.price_per_minute_cents ?? 0) / 100}
                  </option>
                ))}
              </select>
            </label>

            <label className="form-row">
              <span>Validity</span>
              <select value={duration} onChange={e => setDuration(e.target.value)}>
                <option value="week">1 week</option>
                <option value="month">1 month</option>
                <option value="quarter">3 months</option>
                <option value="year">1 year</option>
                <option value="custom">Custom days…</option>
              </select>
            </label>

            {duration === "custom" && (
              <label className="form-row">
                <span>Days</span>
                <input
                  type="number"
                  min="1"
                  value={customDays}
                  onChange={(e) => setCustomDays(e.target.value)}
                />
              </label>
            )}

            <div className="form-row compact">
              <small>Starts: {nowISO}</small>
              <small>Ends: {endISO}</small>
            </div>

            <div className="actions">
              <button className="btn" onClick={onClose} disabled={busy}>Cancel</button>
              <button
                className="btn primary"
                onClick={handleCreate}
                disabled={busy || !planId}
                title={!planId ? "Pick a plan first" : ""}
              >
                {busy ? "Creating…" : "Create subscription"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
