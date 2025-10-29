import { useState } from "react";
import "./PlateEmailForm.css";

export default function PlateEmailForm({ onSubmit, disabled, buttonLabel = "Proceed to Payment" }) {
  const [name, setName] = useState("");
  const [plate, setPlate] = useState("");
  const [email, setEmail] = useState("");

  const handle = (e) => {
    e.preventDefault();
    if (!name || !plate || !email) return;
    onSubmit({ name, plate, email });
  };

  return (
    <form className="plate-form" onSubmit={handle}>
      <label>
        Full name
        <input
          type="text"
          placeholder="e.g. Amy Schumer"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          disabled={disabled}
        />
      </label>

      <label>
        Plate
        <input
          type="text"
          placeholder="e.g. BG AB1234CD"
          value={plate}
          onChange={(e) => setPlate(e.target.value)}
          required
          disabled={disabled}
        />
      </label>

      <label>
        Email
        <input
          type="email"
          placeholder="you@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          disabled={disabled}
        />
      </label>

      <button className="submit-btn" type="submit" disabled={disabled}>
        {buttonLabel}
      </button>
      <p className="tiny">We’ll email you a verification link, then redirect you to Stripe to finish payment.</p>
    </form>
  );
}
