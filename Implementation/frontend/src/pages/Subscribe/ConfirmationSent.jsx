// src/pages/Subscribe/ConfirmationSent.jsx
import React from "react";
import "./Subscription.css";

export default function ConfirmationSent({ email, onRestart }) {
  return (
    <div className="form-card center">
      <h2 style={{ marginTop: 0 }}>Check your email ✉️</h2>
      <p>We sent a verification link to <strong>{email}</strong>.</p>
      <p>Open it to confirm your plate and continue to Stripe Checkout.</p>
      <button className="ghost-btn" onClick={onRestart}>Use a different email</button>
    </div>
  );
}
