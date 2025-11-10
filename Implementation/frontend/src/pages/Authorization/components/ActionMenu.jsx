import { useState } from "react";
import {
  whitelistVehicle,
  blacklistVehicle,
  deleteBlacklistedVehicle,
} from "../../../api/adminApi";

export default function ActionMenu({ vehicle, onChange, onStartWhitelist }) {
  const [busy, setBusy] = useState(false);

  async function run(fn, ...args) {
    setBusy(true);
    try {
      await fn(...args);
      onChange?.();
      return true;
    } catch (e) {
      const msg = e?.response?.data?.detail || e.message || "Action failed";
      alert(msg);
      return false;
    } finally {
      setBusy(false);
    }
  }

  async function onWhitelistClick() {
    onStartWhitelist?.(vehicle);

    // Flip blacklist -> whitelist on backend
    const ok = await run(whitelistVehicle, vehicle.id, { resumeSuspended: true });
    if (!ok) {

      onStartWhitelist?.(null);
      return;
    }

  }

  return (
    <div className="action-menu">
      <select
        disabled={busy}
        value=""
        onChange={async (e) => {
          const v = e.target.value;
          if (!v) return;
          if (v === "whitelist") {
            await onWhitelistClick();
          } else if (v === "blacklist") {
            await run(blacklistVehicle, vehicle.id);
          } else if (v === "delete_blacklisted") {
            if (confirm("Delete this blacklisted vehicle? This cannot be undone.")) {
              await run(deleteBlacklistedVehicle, vehicle.id);
            }
          }
          e.target.value = "";
        }}
      >
        <option value="" disabled>Whitelisted ▾</option>
        {vehicle.is_blacklisted ? (
          <>
            <option value="whitelist">Whitelist</option>
            <option value="delete_blacklisted">Delete (blacklisted)</option>
          </>
        ) : (
          <option value="blacklist">Blacklist</option>
        )}
      </select>
    </div>
  );
}
