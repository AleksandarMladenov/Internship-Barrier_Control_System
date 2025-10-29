import { useEffect, useMemo, useState } from "react";
import ToggleTabs from "../../components/subscribe/ToggleTabs.jsx";
import PlanCard from "../../components/subscribe/PlanCard.jsx";
import PlateEmailForm from "../../components/subscribe/PlateEmailForm.jsx";
import "./SubscriptionPage.css";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000/api";

// fallback (only if billing_period missing)
const PRICE_ID_MAP = {
  month: "price_1SNIQgBmEsx1VUE99ijWJHmC",
  year: "price_1SNVltBmEsx1VUE98KdTgrQK",
};

const norm = (v) => (v ?? "").toString().trim().toLowerCase();
const isMonth = (v) => ["month", "monthly"].includes(norm(v));
const isYear = (v) => ["year", "yearly", "annual"].includes(norm(v));

export default function SubscriptionPage() {
  const [tab, setTab] = useState("month");
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);

  // user must explicitly select a plan
  const [selectedPlanId, setSelectedPlanId] = useState(null);

  const [claiming, setClaiming] = useState(false);
  const [notice, setNotice] = useState("");

  useEffect(() => {
    let alive = true;
    setLoading(true);
    fetch(`${API_BASE}/plans?type=subscription`)
      .then((r) => r.json())
      .then((data) => {
        if (!alive) return;
        const arr = Array.isArray(data) ? data : [];
        setPlans(arr);
      })
      .catch(() => {})
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, []);

  const plansForTab = useMemo(() => {
    return tab === "month"
      ? plans.filter((p) => isMonth(p.billing_period))
      : plans.filter((p) => isYear(p.billing_period));
  }, [plans, tab]);

  const selectedPlan = plans.find((p) => p.id === selectedPlanId) || null;

  const priceStr = (p) => {
    if (!p) return "";
    const amount = (Number(p.period_price_cents || 0) / 100).toFixed(2);
    return `${(p.currency || "EUR").toUpperCase()} ${amount} / ${p.billing_period}`;
  };

  const handleSubmit = async ({ name, email, plate }) => {
    if (!selectedPlan) return;
    setClaiming(true);
    setNotice("");

    const normalized = plate.trim().toUpperCase().replace(/\s+/g, " ");
    let region_code = "BG";
    let plate_text = normalized;
    const head = normalized.split(" ")[0];

    if (/^[A-Z]{1,3}$/.test(head) && normalized.includes(" ")) {
      region_code = head;
      plate_text = normalized.split(" ").slice(1).join("");
    } else {
      plate_text = normalized.replace(/\s/g, "");
    }

    try {
      const res = await fetch(`${API_BASE}/subscriptions/claim`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          email,
          region_code,
          plate_text,
          plan_id: selectedPlan.id,
        }),
      });

      if (res.status === 202) {
        setNotice("✅ Check your email to continue to payment!");
      } else {
        const err = await res.json().catch(() => ({}));
        throw new Error(err?.detail || "Failed to start subscription");
      }
    } catch (e) {
      setNotice(`❌ ${e.message}`);
    } finally {
      setClaiming(false);
    }
  };

  return (
    <div className="subscribe-page">
      <header className="subscribe-header">
        <button className="back-btn" onClick={() => history.back()}>←</button>
        <h1>Subscription</h1>
      </header>

      <ToggleTabs active={tab} onChange={setTab} />

      <div className="subscribe-grid">

        <div className="left-col">
          {plansForTab.map((plan) => (
            <div
              key={plan.id}
              onClick={() => setSelectedPlanId(plan.id)}
              style={{ cursor: "pointer" }}
            >
              <PlanCard
                loading={loading}
                title={plan.name}
                price={priceStr(plan)}
                bullets={["1 vehicle", "Cancel anytime"]}
                ctaLabel={selectedPlanId === plan.id ? "Selected ✓" : "Select"}
              />
            </div>
          ))}

          {!plansForTab.length && (
            <div className="panel" style={{ minHeight: 180 }}>
              <h2>No plan for {tab}</h2>
            </div>
          )}
        </div>

        {/*  Form only enabled when a plan selected */}
        <div className="right-col">
          <div className="panel">
            <h2>License plate</h2>
            <p className="hint">Example: BG AB1234CD</p>

            <PlateEmailForm
              disabled={claiming || !selectedPlanId}
              onSubmit={handleSubmit}
              buttonLabel={
                selectedPlan
                  ? `Proceed to Payment (${priceStr(selectedPlan)})`
                  : "Select a plan first"
              }
            />

            {notice && <div className="notice">{notice}</div>}
          </div>
        </div>
      </div>
    </div>
  );
}
