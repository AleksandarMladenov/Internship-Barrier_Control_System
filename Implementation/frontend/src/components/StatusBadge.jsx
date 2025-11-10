// src/components/StatusBadge.jsx
import "./StatusBadge.css";

export default function StatusBadge({ value }) {
  const v = (value || "").toLowerCase();
  let cls = "sbadge";
  if (v === "authorized" || v === "active") cls += " sbadge--ok";
  else if (v === "pending" || v === "pending_payment") cls += " sbadge--warn";
  else if (["rejected", "canceled", "suspended", "paused"].includes(v)) cls += " sbadge--err";
  else cls += " sbadge--muted";

  const text =
    v === "active" ? "Authorized" :
    v === "pending_payment" ? "Pending" :
    v.charAt(0).toUpperCase() + v.slice(1);

  return <span className={cls}>{text}</span>;
}
