import React, { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import "./VisitorPortal.css";

const API = (import.meta.env.VITE_API_BASE || import.meta.env.VITE_API_BASE_URL || "").trim();
const EMAIL_EP = import.meta.env.VITE_RECEIPT_EMAIL_ENDPOINT || "";

// helpers
const fmtMoney = (cents, currency = "EUR") =>
  typeof cents === "number"
    ? (cents / 100).toLocaleString(undefined, { style: "currency", currency })
    : "—";

const fmtTime = (iso) =>
  iso ? new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "—";

const isEmail = (v) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v || "");

function cn(...xs) {
  return xs.filter(Boolean).join(" ");
}

function Notice({ intent = "info", children }) {
  return <div className={cn("vp-notice", `vp-notice-${intent}`)}>{children}</div>;
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

function PlatePill({ value }) {
  return (
    <div className="vp-plate-pill">
      <span className="vp-plate-pill-text">{value || "—"}</span>
    </div>
  );
}

function Barcode({ plateFull, sessionId }) {
  return (
    <div className="vp-barcode">
      <svg viewBox="0 0 420 100" className="vp-barcode-svg" aria-label="Barcode">
        {[
          10, 22, 28, 44, 54, 60, 78, 90, 98, 120, 132, 150, 162, 166, 180, 196, 210, 224, 232, 248, 260, 268, 280,
          292, 305, 318, 330, 342, 350, 364, 378, 392, 404,
        ].map((x, i) => (
          <rect key={i} x={x} y={8} width={i % 3 === 0 ? 8 : 4} height={84} fill="black" />
        ))}
      </svg>

      <div className="vp-barcode-caption">
        {plateFull || "N/A"} &nbsp;•&nbsp; Session #{sessionId}
      </div>
    </div>
  );
}

function Field({ label, value, onChange, placeholder, type = "text" }) {
  return (
    <label className="vp-field vp-field-1">
      <div className="vp-field-top">
        <span className="vp-field-label">{label}</span>
      </div>
      <input className="vp-input" type={type} value={value} onChange={onChange} placeholder={placeholder} />
    </label>
  );
}

function PrimaryButton({ children, disabled, onClick }) {
  return (
    <button onClick={onClick} disabled={disabled} className={cn("vp-btn vp-btn-primary", disabled && "vp-btn-disabled")}>
      {children}
    </button>
  );
}

export default function ReceiptPage() {
  const [params] = useSearchParams();
  const [session, setSession] = useState(null);
  const [email, setEmail] = useState("");
  const [err, setErr] = useState("");
  const [toast, setToast] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);

        const cs = params.get("cs");
        let sid = params.get("session_id") || null;

        // Resolve by checkout session id if needed
        if (!sid && cs) {
          const r = await fetch(`${API}/payments/resolve?cs=${encodeURIComponent(cs)}&t=${Date.now()}`, {
            cache: "no-store",
            headers: { "Cache-Control": "no-cache" },
          });
          if (r.ok) {
            const j = await r.json();
            sid = String(j.session_id);
            sessionStorage.setItem("visitor.session_id", sid);
          }
        }

        if (!sid) {
          const stored = sessionStorage.getItem("visitor.session_id");
          if (stored) sid = stored;
        }

        if (!sid) {
          setErr("Could not resolve your receipt. Please return to the kiosk page and try again.");
          return;
        }

        const getSession = async () =>
          fetch(`${API}/sessions/${sid}?t=${Date.now()}`, {
            cache: "no-store",
            headers: { "Cache-Control": "no-cache" },
          }).then((r) => r.json());

        let s = await getSession();
        setSession(s);

        // If returning from Stripe: confirm + re-fetch
        if (cs && s?.status === "awaiting_payment") {
          try {
            await fetch(`${API}/payments/confirm?cs=${encodeURIComponent(cs)}`, {
              method: "POST",
              cache: "no-store",
              headers: { "Cache-Control": "no-cache" },
            });
            s = await getSession();
            setSession(s);
          } catch {
            // ignore
          }
        }

        // Poll briefly if still awaiting
        if (s?.status === "awaiting_payment") {
          for (let i = 0; i < 6; i++) {
            await new Promise((r) => setTimeout(r, 2000));
            const s2 = await getSession();
            if (s2?.status === "paid" || s2?.status === "closed") {
              setSession(s2);
              break;
            }
          }
        }

        // Clean URL
        if (window.history?.replaceState) {
          const url = new URL(window.location.href);
          if (cs) url.searchParams.delete("cs");
          if (sid) url.searchParams.set("session_id", sid);
          window.history.replaceState({}, "", url.toString());
        }
      } catch (e) {
        console.error(e);
        setErr("Failed to load receipt.");
      } finally {
        setLoading(false);
      }
    })();
  }, [params]);

  const sendReceipt = async () => {
    if (!EMAIL_EP || !session?.id || !isEmail(email)) return;
    setToast("");
    setSending(true);
    try {
      const resp = await fetch(EMAIL_EP, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: session.id, email }),
      });
      setToast(resp.ok ? "Receipt sent to your email." : "Could not send email. Please try again.");
    } catch {
      setToast("Could not send email. Please try again.");
    } finally {
      setSending(false);
    }
  };

  const paid = session && (session.status === "paid" || session.status === "closed");
  const region = session?.vehicle?.region_code || "BG";
  const plate = session?.vehicle?.plate_text || "02NN18267";
  const plateFull = `${region}${plate}`;
  const currency = session?.plan?.currency || "EUR";

  const addressTitle = "Parking space Address";
  const addressCity = "Vratsa, 3000";

  return (
    <div className="vp-screen">
      <div className="vp-phone">
        <TopStepper step="receipt" onBack={() => window.history.back()} />

        <div className="vp-outer">
          <div className="vp-card-plain">
            <div className="vp-card-header">
              <div>
                <div className="vp-card-title">Receipt</div>
                <div className="vp-card-subtitle">Thank you for parking with us</div>
              </div>

              <div className="vp-icon vp-icon-sm">
                <span className="vp-icon-emoji">🧾</span>
              </div>
            </div>

            <div className="vp-card-body">
              {loading && <Notice intent="info">Loading…</Notice>}
              {err && <Notice intent="error">{err}</Notice>}
              {toast && !err && <div className="vp-mt-sm"><Notice intent="success">{toast}</Notice></div>}

              {!loading && !err && session && (
                <>
                  {/* Plate + Paid */}
                  <div className="vp-receipt-top">
                    <PlatePill value={`${region} ${plate}`} />
                    {paid && <span className="vp-paid-badge">Paid</span>}
                  </div>

                  {/* Summary box like previous steps */}
                  <div className="vp-summary-box">
                    <div className="vp-info-row">
                      <span className="vp-info-label">Entry</span>
                      <span className="vp-info-value">{fmtTime(session.started_at)}</span>
                    </div>
                    <div className="vp-info-row">
                      <span className="vp-info-label">Exit</span>
                      <span className="vp-info-value">{fmtTime(session.ended_at)}</span>
                    </div>
                    <div className="vp-info-row vp-info-row-strong">
                      <span className="vp-info-label">Paid</span>
                      <span className="vp-info-value">{fmtMoney(session.amount_charged, currency)}</span>
                    </div>
                  </div>

                  {/* Barcode block */}
                  <div className="vp-mt">
                    <div className="vp-barcode-wrap">
                      <Barcode plateFull={plateFull} sessionId={session.id} />
                      <div className="vp-address">
                        {addressTitle} • {addressCity}
                      </div>
                    </div>
                  </div>

                  {/* Email */}
                  {!!EMAIL_EP && paid && (
                    <div className="vp-mt">
                      <Field
                        label="Send receipt to email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="you@example.com"
                        type="email"
                      />
                      <div className="vp-mt-sm">
                        <PrimaryButton onClick={sendReceipt} disabled={!isEmail(email) || sending}>
                          {sending ? "Sending…" : "Send on E-mail"}
                        </PrimaryButton>
                      </div>
                    </div>
                  )}

                  <div className="vp-footer">Session #{session.id}</div>

                  <div className="vp-navbar">NavBar</div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
