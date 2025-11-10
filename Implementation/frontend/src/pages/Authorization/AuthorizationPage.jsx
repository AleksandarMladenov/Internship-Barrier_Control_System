// src/pages/Authorization/AuthorizationPage.jsx
import { useEffect, useMemo, useState } from "react";
import "./Authorization.css";
import StatusBadge from "../../components/StatusBadge";
import ActionMenu from "./components/ActionMenu";
import SelectPlanModal from "./components/SelectPlanModal";
import { fetchVehicles } from "../../api/adminApi";

function Card({ icon, title, subtitle, onClick }) {
  return (
    <button className="auth-card" onClick={onClick} type="button">
      <div className="auth-card__icon">{icon}</div>
      <div className="auth-card__text">
        <div className="auth-card__title">{title}</div>
        {subtitle && <div className="auth-card__subtitle">{subtitle}</div>}
      </div>
    </button>
  );
}

export default function AuthorizationPage() {
  const [q, setQ] = useState("");
  const [filter, setFilter] = useState("all"); // all | pending | whitelisted | blacklisted
  const [rows, setRows] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  // Modal state
  const [showPlanModal, setShowPlanModal] = useState(false);
  const [selectedVehicle, setSelectedVehicle] = useState(null);

  async function load() {
    setLoading(true);
    try {
      const data = await fetchVehicles({ q, filter, page: 1, pageSize: 50 });
      const items = Array.isArray(data) ? data : (data.items ?? []);
      const normalized = items.map((v) => ({
        ...v,
        is_blacklisted: v.is_blacklisted ?? v.blacklisted ?? false,
        status: (v.status ?? v.access_status ?? "").toString(),
      }));
      setRows(normalized);
      setTotal(data.total ?? normalized.length);
    } catch (e) {
      console.error("vehicles load failed:", e);
      setRows([]);
      setTotal(0);
      alert(e?.message || "Failed to load vehicles");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();

  }, [filter]);

  // Helpers to interpret status
  const isAuthorized = (r) => {
    const s = (r.status || "").toLowerCase();
    return !r.is_blacklisted && (s.includes("authorized") || s.includes("active"));
  };
  const isPending = (r) => (r.status || "").toLowerCase().includes("pending");

  const counts = useMemo(() => {
    let pending = 0, white = 0, black = 0;
    for (const r of rows) {
      if (r.is_blacklisted) black++;
      if (isPending(r)) pending++;
      if (isAuthorized(r)) white++;
    }
    return { pending, white, black };

  }, [rows]);

  function startWhitelistFlow(vehicle) {
    setSelectedVehicle(vehicle);
    setShowPlanModal(true);
  }

  return (
    <>
      <div className="auth-wrap">
        <div className="auth-header">
          <h1>Dashboard</h1>
          <div className="auth-search">
            <input
              value={q}
              placeholder="Search"
              onChange={(e) => setQ(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && load()}
            />
          </div>
          <div className="auth-avatar" />
        </div>

        <div className="auth-cards">
          <Card
            title="Pending Vehicles"
            subtitle={`${counts.pending}`}
            icon={<span role="img" aria-label="car">🚗</span>}
            onClick={() => setFilter("pending")}
          />
          <Card
            title="White Listed Vehicles"
            subtitle={`${counts.white}`}
            icon={<span role="img" aria-label="check">✅</span>}
            onClick={() => setFilter("whitelisted")}
          />
          <Card
            title="Black Listed Vehicles"
            subtitle={`${counts.black}`}
            icon={<span role="img" aria-label="flag">🏳️</span>}
            onClick={() => setFilter("blacklisted")}
          />
          <Card
            title="Role Audit"
            subtitle="View actions"
            icon={<span role="img" aria-label="id">🪪</span>}
            onClick={() => alert("Route to Role Management / Audit page")}
          />
        </div>

        <div className="auth-toolbar">
          <label className="filter">
            <span>Filter</span>
            <select value={filter} onChange={(e) => setFilter(e.target.value)}>
              <option value="all">All</option>
              <option value="pending">Pending</option>
              <option value="whitelisted">Whitelisted</option>
              <option value="blacklisted">Blacklisted</option>
            </select>
          </label>
          <button className="btn" onClick={load} disabled={loading}>
            {loading ? "Loading..." : "Refresh"}
          </button>
        </div>

        <div className="auth-table">
          <div className="auth-thead">
            <div>License Plate</div>
            <div>Status</div>
            <div className="ta-right">Action</div>
          </div>

          {rows
            .filter((r) => {
              const txt = `${r.region_code} ${r.plate_text}`.toLowerCase();
              const matchQ = !q || txt.includes(q.toLowerCase());
              const matchF =
                filter === "all"
                  ? true
                  : filter === "blacklisted"
                  ? r.is_blacklisted
                  : filter === "whitelisted"
                  ? isAuthorized(r)
                  : filter === "pending"
                  ? isPending(r)
                  : true;
              return matchQ && matchF;
            })
            .map((row) => {
              const statusValue = row.is_blacklisted
                ? "suspended"
                : (row.status || "authorized");
              return (
                <div className="auth-trow" key={row.id}>
                  <div className="lp">
                    {row.region_code} {row.plate_text}
                  </div>
                  <div>
                    <StatusBadge value={statusValue} />
                  </div>
                  <div className="ta-right">
                    <ActionMenu
                      vehicle={row}
                      onChange={load}
                      onStartWhitelist={startWhitelistFlow}
                    />
                  </div>
                </div>
              );
            })}

          {!loading && rows.length === 0 && (
            <div className="auth-empty">No vehicles found.</div>
          )}
        </div>
      </div>

      {showPlanModal && selectedVehicle && (
        <SelectPlanModal
          vehicle={selectedVehicle}
          open={showPlanModal}
          onClose={() => {
            setShowPlanModal(false);
            setSelectedVehicle(null);
          }}
          onCreated={() => {
            setShowPlanModal(false);
            setSelectedVehicle(null);
            if (filter === "blacklisted") setFilter("whitelisted");
            load();
          }}
        />
      )}
    </>
  );
}
