// src/pages/Authorization/components/SelectPlanModal.jsx
import { useEffect, useMemo, useState } from "react";
import {
  listSubscriptionPlans,
  createSubscription,
  createSubscriptionCheckout,
  reviveLastCanceledAndSendLink,
} from "../../../api/subscriptionsApi";

export default function SelectPlanModal({ vehicle, open = true, onClose, onCreated }) {
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [planId, setPlanId] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [driverEmail, setDriverEmail] = useState("");

  useEffect(() => {
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

  const selectedPlan = useMemo(
    () => plans.find((p) => String(p.id) === String(planId)),
    [plans, planId]
  );

  const nowISO = useMemo(() => new Date().toISOString(), []);

  // Compute end date from the plan's billing_period
  const endISO = useMemo(() => {
    if (!selectedPlan) return "";
    const d = new Date();

    const period = String(selectedPlan.billing_period || "").toLowerCase();

    switch (period) {
      case "week":
        d.setDate(d.getDate() + 7);
        break;
      case "quarter":
        d.setMonth(d.getMonth() + 3);
        break;
      case "year":
        d.setFullYear(d.getFullYear() + 1);
        break;
      // default to month if absent/unknown
      case "month":
      default:
        d.setMonth(d.getMonth() + 1);
        break;
    }
    return d.toISOString();
  }, [selectedPlan]);

  // Admin creates subscription now and opens Stripe Checkout
  async function handleCreateNow() {
    if (!selectedPlan) {
      setErr("Please pick a plan.");
      return;
    }
    setBusy(true);
    setErr("");
    try {
      const sub = await createSubscription({
        vehicle_id: vehicle.id,
        plan_id: Number(selectedPlan.id),
        valid_from: nowISO,
        valid_to: endISO,
        auto_renew: true,
      });

      if (!sub?.id) throw new Error("Subscription ID missing");
      const { checkout_url } = await createSubscriptionCheckout(sub.id);
      if (!checkout_url) throw new Error("Checkout URL missing");

      // Admin pays in a new tab/window
      window.open(checkout_url, "_blank", "noopener,noreferrer");

      onCreated?.();
      onClose?.();
    } catch (e) {
      setErr(e?.message || "Failed to create subscription");
    } finally {
      setBusy(false);
    }
  }

  // Email the driver a payment link; backend revives last canceled sub (same ID) or prepares pending
  async function handleEmailDriverLink() {
    if (!driverEmail) {
      setErr("Please enter the driver's email.");
      return;
    }
    setBusy(true);
    setErr("");
    try {
      await reviveLastCanceledAndSendLink(vehicle.id, {
        driver_email: driverEmail,
        // if you want to force the selected plan, pass it; otherwise backend can reuse the last canceled plan
        plan_id: selectedPlan ? Number(selectedPlan.id) : undefined,
      });

      onCreated?.();
      onClose?.();
    } catch (e) {
      setErr(e?.message || "Failed to send payment link");
    } finally {
      setBusy(false);
    }
  }

  if (!open) return null;

  return (
    <div className="modal-backdrop">
      <div className="modal">
        <h3>Link Subscription</h3>
        <p>
          Vehicle: <b>{vehicle.region_code} {vehicle.plate_text}</b>
        </p>

        {loading ? (
          <p>Loading plans…</p>
        ) : err ? (
          <p className="error">{err}</p>
        ) : plans.length === 0 ? (
          <p>No subscription plans configured.</p>
        ) : (
          <>
            <label className="form-row">
              <span>Plan (includes period)</span>
              <select value={planId} onChange={(e) => setPlanId(e.target.value)}>
                <option value="" disabled>Pick a plan…</option>
                {plans.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                    {" · "}
                    {p.currency} {(p.price_flat_cents ?? p.price_per_minute_cents ?? 0) / 100}
                    {" · "}
                    {String(p.billing_period || "").toLowerCase() || "month"}
                  </option>
                ))}
              </select>
            </label>

            <div className="form-row compact">
              <small>Starts: {nowISO}</small>
              <small>Ends: {endISO || "—"}</small>
            </div>

            <label className="form-row">
              <span>Driver email</span>
              <input
                type="email"
                placeholder="driver@email.com"
                value={driverEmail}
                onChange={(e) => setDriverEmail(e.target.value)}
              />
            </label>

            <div className="actions">
              <button className="btn" onClick={onClose} disabled={busy}>Cancel</button>

              <button
                className="btn"
                onClick={handleEmailDriverLink}
                disabled={busy || !driverEmail}
                title={!driverEmail ? "Enter driver email" : ""}
              >
                {busy ? "Sending…" : "Email driver payment link"}
              </button>

              <button
                className="btn primary"
                onClick={handleCreateNow}
                disabled={busy || !selectedPlan}
                title={!selectedPlan ? "Pick a plan first" : ""}
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
