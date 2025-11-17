// src/components/ui.tsx
import React from "react";

export function Card({ className="", children }) {
  return (
    <div className={`w-full bg-white rounded-2xl shadow-sm border border-gray-100 ${className}`}>
      {children}
    </div>
  );
}

export function CardBody({ className="", children }) {
  return <div className={`p-5 ${className}`}>{children}</div>;
}

export function Button({ children, className="", disabled, ...props }) {
  return (
    <button
      {...props}
      disabled={disabled}
      className={`w-full h-11 rounded-xl font-semibold transition-colors
      ${disabled ? "bg-gray-300 text-gray-600 cursor-not-allowed" : "bg-teal-600 text-white hover:bg-teal-700"} ${className}`}
    >
      {children}
    </button>
  );
}

export function Notice({ intent="info", children }) {
  const styles = {
    info: "bg-blue-50 text-blue-800 border-blue-200",
    warn: "bg-amber-50 text-amber-900 border-amber-200",
    error:"bg-rose-50 text-rose-900 border-rose-200",
    success:"bg-emerald-50 text-emerald-900 border-emerald-200",
  }[intent];
  return <div className={`border rounded-lg p-3 text-sm ${styles}`}>{children}</div>;
}

export function StatRow({ label, value, bold=false }) {
  return (
    <li className={`flex justify-between ${bold ? "font-semibold" : ""}`}>
      <span className="text-gray-600">{label}</span>
      <span>{value}</span>
    </li>
  );
}

export function PlatePill({ region, plate }) {
  return (
    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-50 text-teal-800 border border-teal-200 text-sm font-semibold">
      <span className="px-2 py-0.5 rounded bg-white border border-teal-300">{region}</span>
      <span>{plate}</span>
    </div>
  );
}

export function PageShell({ children }) {
  return (
    <div className="min-h-screen bg-gray-50 flex items-start sm:items-center justify-center p-4">
      <div className="w-full max-w-md">{children}</div>
    </div>
  );
}

export function SectionTitle({ children, subtitle }) {
  return (
    <div className="mb-3">
      <div className="text-xl font-semibold">{children}</div>
      {subtitle && <div className="text-xs text-gray-500 mt-1">{subtitle}</div>}
    </div>
  );
}
