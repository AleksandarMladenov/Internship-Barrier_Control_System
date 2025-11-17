import React, { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

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

// simple divider
function Divider() {
  return <div className="h-px bg-gray-200 my-5" />;
}

// plate pill
function PlatePill({ region, plate }) {
  return (
    <div className="inline-flex items-center px-4 h-9 rounded-xl border-2 border-teal-500 text-sm font-semibold text-gray-800">
      {region?.toUpperCase()}
      {plate ? plate.toUpperCase() : ""}
    </div>
  );
}


function Barcode({ plateFull, sessionId }) {
  return (
    <div className="w-full flex flex-col items-center">
      <svg viewBox="0 0 420 100" className="w-[90%] max-w-sm h-24">
        {[
          10, 22, 28, 44, 54, 60, 78, 90, 98, 120, 132, 150, 162, 166, 180, 196, 210, 224, 232, 248, 260, 268, 280,
          292, 305, 318, 330, 342, 350, 364, 378, 392, 404,
        ].map((x, i) => (
          <rect key={i} x={x} y={8} width={i % 3 === 0 ? 8 : 4} height={84} fill="black" />
        ))}
      </svg>
      <div className="text-xs text-gray-500 -mt-1 tracking-widest">
        {plateFull || "N/A"} &nbsp;•&nbsp; Session #{sessionId}
      </div>
    </div>
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
          const r = await fetch(
            `${API}/payments/resolve?cs=${encodeURIComponent(cs)}&t=${Date.now()}`,
            {
              cache: "no-store",
              headers: { "Cache-Control": "no-cache" },
            },
          );
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

          }
        }


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
      if (resp.ok) {
        setToast("Receipt sent to your email.");
      } else {
        setToast("Could not send email. Please try again.");
      }
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
    <div className="min-h-screen bg-gray-50 flex items-start sm:items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-md border border-gray-100 p-5">
        {/* Header */}
        <div className="mb-4">
          <div className="text-sm font-semibold text-gray-900">Receipt</div>
          <div className="text-xs text-gray-600">Thank you for parking with us</div>
        </div>

        {loading && (
          <div className="text-sm text-blue-800 bg-blue-50 border border-blue-200 rounded-lg p-3">
            Loading…
          </div>
        )}
        {err && (
          <div className="text-sm text-rose-900 bg-rose-50 border border-rose-200 rounded-lg p-3">
            {err}
          </div>
        )}
        {toast && !err && (
          <div className="text-sm text-emerald-900 bg-emerald-50 border border-emerald-200 rounded-lg p-3 mb-2">
            {toast}
          </div>
        )}

        {!loading && !err && session && (
          <>
            {/* Plate + Paid */}
            <div className="flex items-center justify-between mb-3">
              <PlatePill region={region} plate={plate} />
              {paid && (
                <span className="inline-flex items-center text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-full px-2.5 py-1 text-xs font-semibold">
                  Paid
                </span>
              )}
            </div>

            {/* Entry / Exit / Paid rows */}
            <ul className="text-sm space-y-1 mb-4">
              <li>
                <strong>Entry</strong>&nbsp;{fmtTime(session.started_at)}
              </li>
              <li>
                <strong>Exit</strong>&nbsp;{fmtTime(session.ended_at)}
              </li>
              <li>
                <strong>Paid</strong>&nbsp;{fmtMoney(session.amount_charged, currency)}
              </li>
            </ul>

            <Divider />

            {/* Barcode + address */}
            <Barcode plateFull={plateFull} sessionId={session.id} />
            <div className="text-xs text-gray-600 mt-2 text-center">
              {addressTitle} • {addressCity}
            </div>


            {!!EMAIL_EP && paid && (
              <div className="mt-6">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Send receipt to email
                </label>
                <input
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  type="email"
                  placeholder="you@example.com"
                  className="w-full h-11 px-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
                <button
                  onClick={sendReceipt}
                  disabled={!isEmail(email) || sending}
                  className={`mt-3 w-full h-11 rounded-xl font-semibold text-white ${
                    !isEmail(email) || sending
                      ? "bg-gray-300 cursor-not-allowed"
                      : "bg-teal-600 hover:bg-teal-700"
                  }`}
                >
                  {sending ? "Sending…" : "Send on E-mail"}
                </button>
              </div>
            )}

            <div className="text-xs text-gray-500 mt-4 text-center">Session #{session.id}</div>
          </>
        )}
      </div>
    </div>
  );
}
