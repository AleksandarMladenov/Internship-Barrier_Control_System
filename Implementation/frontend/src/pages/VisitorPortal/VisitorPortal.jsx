import React, { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import "./VisitorPortal.css";

const API = (() => {
  const val = (import.meta.env.VITE_API_BASE || import.meta.env.VITE_API_BASE_URL || "").trim();
  if (!val) console.error("Missing API base. Set VITE_API_BASE or VITE_API_BASE_URL in your project root .env");
  return val;
})();
const EMAIL_EP = import.meta.env.VITE_RECEIPT_EMAIL_ENDPOINT || "";

const fmtMoney = (cents, currency = "EUR") =>
  typeof cents === "number"
    ? (cents / 100).toLocaleString(undefined, { style: "currency", currency })
    : "—";

const fmtTime = (iso) =>
  iso ? new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "—";

function cn(...xs) {
  return xs.filter(Boolean).join(" ");
}

function Notice({ intent = "info", children }) {
  return <div className={cn("vp-notice", `vp-notice-${intent}`)}>{children}</div>;
}

function PlatePill({ value }) {
  return (
    <div className="vp-plate-pill">
      <span className="vp-plate-pill-text">{value || "—"}</span>
    </div>
  );
}

function TopStepper({ step, onBack }) {
  const items = ["Review", "Payment", "Receipt"];
  const activeIndex = step === "lookup" ? 0 : step === "summary" ? 1 : 2;

  return (
    <header className="vp-stepper">
      <button type="button" onClick={onBack} className="vp-stepper-back" aria-label="Back">
        &lt;
      </button>

      <div className="vp-stepper-mid">
        <div className="vp-stepper-labels">
          {items.map((label, i) => (
            <span
              key={label}
              className={cn("vp-stepper-label", i === activeIndex && "vp-stepper-label-active")}
            >
              {label}
            </span>
          ))}
        </div>

        <div className="vp-stepper-dots">
          {items.map((_, i) => (
            <span key={i} className={cn("vp-stepper-dot", i === activeIndex && "vp-stepper-dot-active")} />
          ))}
        </div>
      </div>

      <div className="vp-stepper-spacer" />
    </header>
  );
}

function Field({ label, hint, ...props }) {
  return (
    <label className="vp-field">
      <div className="vp-field-top">
        <span className="vp-field-label">{label}</span>
        {hint ? <span className="vp-field-hint">{hint}</span> : null}
      </div>
      <input className="vp-input" {...props} />
    </label>
  );
}

function Card({ children }) {
  return <div className="vp-card">{children}</div>;
}

function CardHeader({ title, subtitle, right }) {
  return (
    <div className="vp-card-header">
      <div>
        <div className="vp-card-title">{title}</div>
        {subtitle ? <div className="vp-card-subtitle">{subtitle}</div> : null}
      </div>
      {right}
    </div>
  );
}

function CardBody({ children }) {
  return <div className="vp-card-body">{children}</div>;
}

function InfoRow({ label, value, strong }) {
  return (
    <div className={cn("vp-info-row", strong && "vp-info-row-strong")}>
      <span className="vp-info-label">{label}</span>
      <span className="vp-info-value">{value}</span>
    </div>
  );
}

function PrimaryButton({ children, ...props }) {
  return (
    <button {...props} className="vp-btn vp-btn-primary">
      {children}
    </button>
  );
}

function SecondaryButton({ children, ...props }) {
  return (
    <button {...props} className="vp-btn vp-btn-secondary">
      {children}
    </button>
  );
}

function ParkingIcon() {
  return (
    <div className="vp-icon">
      <span className="vp-icon-emoji">🚗</span>
    </div>
  );
}

export default function VisitorPortal() {
  const [params] = useSearchParams();

  const REGION_LOCKED = "BG";

  const [step, setStep] = useState("lookup"); // lookup | summary | receipt
  const [plate, setPlate] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  const [sessionId, setSessionId] = useState(null);
  const [quote, setQuote] = useState(null);
  const [session, setSession] = useState(null);
  const [email, setEmail] = useState("");

  const normalizedPlate = useMemo(() => (plate || "").toUpperCase().replace(/\s+/g, ""), [plate]);
  const prettyPlate = useMemo(() => `${REGION_LOCKED} ${normalizedPlate}`.trim(), [normalizedPlate]);

  async function callExitScan(opts = {}) {
    const r = REGION_LOCKED;
    const p = (opts.plateText ?? plate).toUpperCase().replace(/\s+/g, "");

    setErr("");
    if (!p || p.length < 4) {
      setErr("Enter a valid plate (min 4 characters).");
      return;
    }

    try {
      setLoading(true);
      const res = await fetch(`${API}/scans/exit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          region_code: r,
          plate_text: p,
          gate_id: "web_portal",
          source: "driver_portal",
        }),
      });
      if (!res.ok) throw new Error(`Exit scan failed (${res.status})`);
      const data = await res.json();

      if (data.status === "error") {
        setErr(data.detail || "Unable to prepare your session. Please contact support at the exit.");
        return;
      }

      setSessionId(data.session_id || null);

      if (data.status === "awaiting_payment") {
        setQuote({
          amount_cents: data.amount_cents,
          currency: data.currency || "EUR",
          minutes_billable: data.minutes_billable,
        });

        if (data.session_id) {
          const s = await fetch(`${API}/sessions/${data.session_id}`).then((r) => r.json());
          setSession(s);
        }
        setStep("summary");
        return;
      }

      if (data.status === "closed") {
        if (data.session_id) {
          const s = await fetch(`${API}/sessions/${data.session_id}`).then((r) => r.json());
          setSession(s);
        }
        setStep("receipt");
        return;
      }

      setErr("Unexpected response. Please try again.");
    } catch (e) {
      console.error(e);
      setErr("Could not reach the server. Check your connection and try again.");
    } finally {
      setLoading(false);
    }
  }

  async function startCheckout() {
    if (!sessionId) return;
    try {
      setLoading(true);
      const res = await fetch(`${API}/payments/checkout?session_id=${encodeURIComponent(sessionId)}`, {
        method: "POST",
      });
      if (!res.ok) throw new Error(`Checkout failed (${res.status})`);
      const data = await res.json();
      if (!data.checkout_url) throw new Error("No checkout_url returned");

      sessionStorage.setItem("visitor.session_id", String(sessionId));
      window.location.href = data.checkout_url;
    } catch (e) {
      console.error(e);
      setErr("Could not start payment. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  async function refreshSession(targetId) {
    const sid = targetId ?? sessionId;
    if (!sid) return;
    try {
      const s = await fetch(`${API}/sessions/${sid}`).then((r) => r.json());
      setSession(s);
      if (s?.status === "paid" || s?.status === "closed") setStep("receipt");
    } catch (e) {
      console.error(e);
    }
  }

  async function sendReceipt() {
    if (!EMAIL_EP) return;
    try {
      setLoading(true);
      await fetch(EMAIL_EP, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, email }),
      });
      alert("Receipt sent!");
    } catch (e) {
      alert("Failed to send email.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const sid = params.get("session_id");
    const pla = params.get("plate");
    const storedSid = sessionStorage.getItem("visitor.session_id");

    if (sid) {
      if (sid.startsWith("cs_")) {
        if (storedSid) {
          setSessionId(storedSid);
          refreshSession(storedSid);
          return;
        }
      } else {
        setSessionId(sid);
        (async () => {
          try {
            const s = await fetch(`${API}/sessions/${sid}`).then((r) => r.json());
            setSession(s);
            if (s?.status === "awaiting_payment") {
              setQuote({
                amount_cents: s.amount_charged,
                currency: (s.plan && s.plan.currency) || "EUR",
                minutes_billable: s.duration,
              });
              setStep("summary");
            } else {
              setStep("receipt");
            }
          } catch (e) {
            console.error(e);
          }
        })();
      }
      return;
    }

    if (pla) {
      setPlate(pla.toUpperCase());
      callExitScan({ plateText: pla });
      return;
    }

    if (storedSid) {
      setSessionId(storedSid);
      refreshSession(storedSid);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="vp-screen">
      <div className="vp-phone">
        <TopStepper step={step} onBack={() => window.history.back()} />

        {/* Outer rounded container like your screenshot */}
        <div className="vp-outer">
          {step === "lookup" && (
            <Card>
              <div className="vp-lookup-header">
                <ParkingIcon />
                <div className="vp-lookup-title">Welcome to Petroff Parking</div>
                <div className="vp-lookup-subtitle">Enter your license plate to proceed to payment.</div>
              </div>

              <div className="vp-grid-2">
                <Field label="Region" value={REGION_LOCKED} disabled />
                <Field
                  label="Plate"
                  hint="min 4 chars"
                  value={plate}
                  onChange={(e) => setPlate(e.target.value)}
                  placeholder="NN18267"
                />
              </div>

              <div className="vp-center">
                <PlatePill value={prettyPlate || "BG —"} />
              </div>

              {err ? (
                <div className="vp-mt">
                  <Notice intent="error">{err}</Notice>
                </div>
              ) : null}

              <div className="vp-mt">
                <PrimaryButton onClick={() => callExitScan()} disabled={loading}>
                  {loading ? "Checking…" : "Proceed to Payment"}
                </PrimaryButton>
              </div>

              <div className="vp-hint">
                We’ll look up your parking session and calculate the fee for plate{" "}
                <span className="vp-hint-strong">{REGION_LOCKED}</span>.
              </div>

              <div className="vp-navbar">NavBar</div>
            </Card>
          )}

          {step === "summary" && (
            <div className="vp-card-plain">
              <CardHeader
                title="Payment"
                subtitle={<PlatePill value={prettyPlate} />}
                right={<ParkingIcon />}
              />
              <CardBody>
                <div className="vp-summary-box">
                  <InfoRow label="Entered" value={fmtTime(session?.started_at)} />
                  <InfoRow label="Exit time" value={fmtTime(session?.ended_at)} />
                  <InfoRow label="Rate" value="Per your visitor plan" />
                  <InfoRow strong label="Total Due" value={fmtMoney(quote?.amount_cents, quote?.currency || "EUR")} />
                </div>

                {err ? (
                  <div className="vp-mt">
                    <Notice intent="error">{err}</Notice>
                  </div>
                ) : null}

                <div className="vp-mt">
                  <PrimaryButton onClick={startCheckout} disabled={loading}>
                    {loading ? "Redirecting…" : `Pay ${fmtMoney(quote?.amount_cents, quote?.currency || "EUR")} now`}
                  </PrimaryButton>
                </div>

                <div className="vp-mt-sm">
                  <SecondaryButton onClick={() => refreshSession()} type="button" disabled={loading}>
                    I’ve paid — Check status
                  </SecondaryButton>
                </div>

                <div className="vp-hint">
                  After payment, the barrier opens automatically. If Stripe doesn’t bring you back here, you can still
                  use “I’ve paid — Check status”.
                </div>

                <div className="vp-navbar">NavBar</div>
              </CardBody>
            </div>
          )}

          {step === "receipt" && (
            <div className="vp-card-plain">
              <CardHeader title="Receipt" subtitle="Parking session details" right={<ParkingIcon />} />
              <CardBody>
                {session?.status === "paid" || session?.status === "closed" ? (
                  <>
                    <div className="vp-summary-box">
                      <InfoRow label="Plate" value={prettyPlate} strong />
                      <InfoRow label="Entry" value={fmtTime(session?.started_at)} />
                      <InfoRow label="Exit" value={fmtTime(session?.ended_at)} />
                      <InfoRow
                        strong
                        label="Paid"
                        value={fmtMoney(session?.amount_charged, (session?.plan && session.plan.currency) || "EUR")}
                      />
                    </div>

                    {!!EMAIL_EP && (
                      <div className="vp-mt">
                        <Field
                          label="Send receipt to email"
                          value={email}
                          onChange={(e) => setEmail(e.target.value)}
                          placeholder="you@example.com"
                        />
                        <div className="vp-mt-sm">
                          <PrimaryButton onClick={sendReceipt} disabled={!email || loading}>
                            {loading ? "Sending…" : "Send on E-mail"}
                          </PrimaryButton>
                        </div>
                      </div>
                    )}

                    <div className="vp-footer">Session #{session?.id}</div>
                  </>
                ) : (
                  <>
                    <Notice intent="warn">Waiting for payment confirmation…</Notice>
                    <div className="vp-mt">
                      <PrimaryButton onClick={() => refreshSession()} disabled={loading}>
                        {loading ? "Refreshing…" : "Refresh"}
                      </PrimaryButton>
                    </div>
                  </>
                )}

                <div className="vp-navbar">NavBar</div>
              </CardBody>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
