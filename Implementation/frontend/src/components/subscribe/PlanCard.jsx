import "./PlanCard.css";

export default function PlanCard({ loading, title, price, bullets = [], ctaLabel }) {
  return (
    <div className="plan-card">
      <div className="car-illus" aria-hidden />
      <div className="plan-body">
        <h3 className="plan-title">{title || "Basic"}</h3>
        <div className="plan-price">{loading ? "…" : (price || "—")}</div>

        <ul className="plan-bullets">
          {bullets.map((b, i) => (
            <li key={i}>
              <span className="check">✓</span>
              <span>{b}</span>
            </li>
          ))}
        </ul>

        <button className="plan-cta" disabled>
          {ctaLabel || "Subscribe"}
        </button>
        <p className="plan-foot">You’ll finalize on the next step.</p>
      </div>
    </div>
  );
}
