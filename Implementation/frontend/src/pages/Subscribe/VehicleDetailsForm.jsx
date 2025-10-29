// src/pages/Subscribe/VehicleDetailsForm.jsx
import React from "react";
import "./Subscription.css";

export default function VehicleDetailsForm({
  form, setForm, onSubmit, submitting, onBack,
}) {
  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  return (
    <div className="form-card">
      <h2 style={{ marginTop: 0 }}>Vehicle & contact</h2>

      <label className="label">Full name</label>
      <input className="input" name="name" value={form.name} onChange={onChange} placeholder="e.g. Alex Petrov" required />

      <div className="row">
        <div>
          <label className="label">Region</label>
          <input className="input" name="region_code" value={form.region_code} onChange={onChange} placeholder="BG" required />
        </div>
        <div>
          <label className="label">Plate</label>
          <input className="input" name="plate_text" value={form.plate_text} onChange={onChange} placeholder="CB 1234 AB" required />
        </div>
      </div>

      <label className="label">Email</label>
      <input className="input" name="email" type="email" value={form.email} onChange={onChange} placeholder="name@example.com" required />

      <div className="actions">
        <button className="primary-btn" onClick={onSubmit} disabled={submitting}>
          {submitting ? "Sending…" : "Proceed to payment"}
        </button>
        <button className="ghost-btn" type="button" onClick={onBack}>Back</button>
        <span className="subtle">We’ll email a link. Click it to pay via Stripe.</span>
      </div>
    </div>
  );
}
