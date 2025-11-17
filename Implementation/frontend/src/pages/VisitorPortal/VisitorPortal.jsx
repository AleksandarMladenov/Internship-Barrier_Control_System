import React, { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";

const API = (() => {
const val = (import.meta.env.VITE_API_BASE || import.meta.env.VITE_API_BASE_URL || "").trim();
if (!val) {
console.error("Missing API base. Set VITE_API_BASE or VITE_API_BASE_URL in your project root .env");
}
return val;
})();
const EMAIL_EP = import.meta.env.VITE_RECEIPT_EMAIL_ENDPOINT || "";

const fmtMoney = (cents, currency = "EUR") =>
  typeof cents === "number"
    ? (cents / 100).toLocaleString(undefined, { style: "currency", currency })
    : "—";

const fmtTime = (iso) =>
  iso ? new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "—";

function Button({ children, ...props }) {
  return (
    <button
      {...props}
      className={`w-full h-11 rounded-xl font-semibold transition-colors ${
        props.disabled
          ? "bg-gray-300 text-gray-600 cursor-not-allowed"
          : "bg-teal-600 text-white hover:bg-teal-700"
      }`}
    >
      {children}
    </button>
  );
}

function Card({ children }) {
  return (
    <div className="max-w-md w-full bg-white rounded-2xl shadow-md border border-gray-100 p-5">
      {children}
    </div>
  );
}

function Notice({ intent = "info", children }) {
  const styles = {
    info: "bg-blue-50 text-blue-800 border-blue-200",
    warn: "bg-amber-50 text-amber-900 border-amber-200",
    error: "bg-rose-50 text-rose-900 border-rose-200",
    success: "bg-emerald-50 text-emerald-900 border-emerald-200",
  }[intent];
  return <div className={`border rounded-lg p-3 text-sm ${styles}`}>{children}</div>;
}

console.log("VITE_API_BASE =", import.meta.env.VITE_API_BASE);
console.log("VITE_API_BASE_URL =", import.meta.env.VITE_API_BASE_URL);


export default function VisitorPortal() {
  const [params] = useSearchParams();

  const [step, setStep] = useState("lookup"); // lookup | summary | receipt
  const [region, setRegion] = useState("BP");
  const [plate, setPlate] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  const [sessionId, setSessionId] = useState(null);
  const [quote, setQuote] = useState(null); // { amount_cents, currency, minutes_billable }
  const [session, setSession] = useState(null);
  const [email, setEmail] = useState("");

  const prettyPlate = useMemo(
    () => `${region.toUpperCase()} ${plate.toUpperCase().replace(/\s+/g, "")}`,
    [region, plate]
  );

  async function callExitScan(opts = {}) {
    const r = (opts.regionCode ?? region).toUpperCase();
    const p = (opts.plateText ?? plate).toUpperCase().replace(/\s+/g, "");
    setErr("");
    if (!r || !p || p.length < 4) {
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
      const res = await fetch(
        `${API}/payments/checkout?session_id=${encodeURIComponent(sessionId)}`,
        { method: "POST" }
      );
      if (!res.ok) throw new Error(`Checkout failed (${res.status})`);
      const data = await res.json();
      if (!data.checkout_url) throw new Error("No checkout_url returned");

      // remember session for after redirect
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

  // Auto-load: ?session_id=... OR ?region=..&plate=.. OR stored session after Stripe
  useEffect(() => {
  const sid = params.get("session_id");
  const reg = params.get("region");
  const pla = params.get("plate");
  const storedSid = sessionStorage.getItem("visitor.session_id"); // numeric parking session id we saved before redirect


  if (sid) {
    if (sid.startsWith("cs_")) {
      if (storedSid) {
        setSessionId(storedSid);
        refreshSession(storedSid); // will flip to receipt once webhook closes it
        return;
      }
      // (optional) if no storedSid, try a backend resolver:
      // fetch(`${API}/payments/resolve?cs=${encodeURIComponent(sid)}`)
      //   .then(r => r.ok ? r.json() : Promise.reject())
      //   .then(({ session_id }) => { setSessionId(session_id); refreshSession(session_id); })
      //   .catch(() => {/* fall back to lookup UI */});
    } else {

      setSessionId(sid);
      (async () => {
        try {
          const s = await fetch(`${API}/sessions/${sid}`).then(r => r.json());
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

  // Region + plate deep link (kiosk flow)
  if (reg && pla) {
    setRegion(reg.toUpperCase());
    setPlate(pla.toUpperCase());
    callExitScan({ regionCode: reg, plateText: pla });
    return;
  }

  // Returning from Stripe without params? Use the stored session id.
  if (storedSid) {
    setSessionId(storedSid);
    refreshSession(storedSid);
  }
  // eslint-disable-next-line react-hooks/exhaustive-deps
}, []);


  return (
    <div className="min-h-screen bg-gray-50 flex items-start sm:items-center justify-center p-4">
      {step === "lookup" && (
        <Card>
          <div className="text-xl font-semibold mb-1">Welcome to Petroff Parking</div>
          <div className="text-xs text-gray-500 mb-4">Visitor checkout</div>

          <label className="block mb-3">
            <div className="text-sm font-medium text-gray-700 mb-1">Region code</div>
            <input
              value={region}
              onChange={(e) => setRegion(e.target.value)}
              className="w-full h-11 px-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
          </label>

          <label className="block mb-3">
            <div className="text-sm font-medium text-gray-700 mb-1">License plate</div>
            <input
              value={plate}
              onChange={(e) => setPlate(e.target.value)}
              placeholder="e.g., NN18267"
              className="w-full h-11 px-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
          </label>

          {err && (
            <div className="mb-3">
              <Notice intent="error">{err}</Notice>
            </div>
          )}

          <Button onClick={() => callExitScan()} disabled={loading}>
            {loading ? "Checking..." : "Proceed to Payment"}
          </Button>

          <div className="text-xs text-gray-500 mt-3">
            We’ll look up your exit and calculate the fee for plate <b>{prettyPlate}</b>.
          </div>
        </Card>
      )}

      {step === "summary" && (
        <Card>
          <div className="text-xl font-semibold mb-2">Payment</div>
          <div className="text-sm text-gray-600 mb-4">
            Plate <span className="font-semibold">{prettyPlate}</span>
          </div>

          <ul className="text-sm space-y-2">
            <li className="flex justify-between">
              <span>Entered</span>
              <span>{fmtTime(session?.started_at)}</span>
            </li>
            <li className="flex justify-between">
              <span>Exit</span>
              <span>{fmtTime(session?.ended_at)}</span>
            </li>
            <li className="flex justify-between">
              <span>Rate</span>
              <span>per your visitor plan</span>
            </li>
            <li className="flex justify-between font-semibold">
              <span>Total Due</span>
              <span>{fmtMoney(quote?.amount_cents, quote?.currency || "EUR")}</span>
            </li>
          </ul>

          {err && (
            <div className="mt-3">
              <Notice intent="error">{err}</Notice>
            </div>
          )}

          <div className="mt-4">
            <Button onClick={startCheckout} disabled={loading}>
              {loading ? "Redirecting..." : `Pay ${fmtMoney(quote?.amount_cents, quote?.currency || "EUR")} now`}
            </Button>
          </div>

          <div className="mt-3">
            <Button onClick={() => refreshSession()} type="button">
              I’ve paid — Check status
            </Button>
          </div>

          <div className="text-xs text-gray-500 mt-3">
            After payment, the barrier will open automatically. If you don’t return here from Stripe, you can still
            press “I’ve paid — Check status”.
          </div>
        </Card>
      )}

      {step === "receipt" && (
        <Card>
          <div className="text-xl font-semibold mb-2">Receipt</div>
          {session?.status === "paid" || session?.status === "closed" ? (
            <>
              <ul className="text-sm space-y-2">
                <li className="flex justify-between">
                  <span>Status</span>
                  <span className="font-semibold capitalize">{session?.status}</span>
                </li>
                <li className="flex justify-between">
                  <span>Plate</span>
                  <span className="font-semibold">{prettyPlate}</span>
                </li>
                <li className="flex justify-between">
                  <span>Entry</span>
                  <span>{fmtTime(session?.started_at)}</span>
                </li>
                <li className="flex justify-between">
                  <span>Exit</span>
                  <span>{fmtTime(session?.ended_at)}</span>
                </li>
                <li className="flex justify-between font-semibold">
                  <span>Paid</span>
                  <span>{fmtMoney(session?.amount_charged, (session?.plan && session.plan.currency) || "EUR")}</span>
                </li>
              </ul>

              {!!EMAIL_EP && (
                <div className="mt-4">
                  <label className="block mb-3">
                    <div className="text-sm font-medium text-gray-700 mb-1">Send receipt to email</div>
                    <input
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="you@example.com"
                      className="w-full h-11 px-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-teal-500"
                    />
                  </label>
                  <Button onClick={sendReceipt} disabled={!email || loading}>
                    Send on E-mail
                  </Button>
                </div>
              )}

              <div className="text-xs text-gray-500 mt-3">Session #{session?.id}</div>
            </>
          ) : (
            <>
              <Notice intent="warn">Waiting for payment confirmation…</Notice>
              <div className="mt-3">
                <Button onClick={() => refreshSession()}>Refresh</Button>
              </div>
            </>
          )}
        </Card>
      )}
    </div>
  );
}
