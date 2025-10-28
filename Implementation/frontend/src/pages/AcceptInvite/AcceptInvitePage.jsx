import React from "react";
import { useSearchParams } from "react-router-dom";
import AcceptInviteForm from "./AcceptInviteForm";
import "./AcceptInvite.css";

export default function AcceptInvitePage() {
  const [params] = useSearchParams();
  const token = params.get("token");

  if (!token) {
    return <div className="invite-container">Invalid or missing invite token.</div>;
  }

  return (
    <div className="invite-container">
      <h2>Set Your Password</h2>
      <AcceptInviteForm token={token} />
    </div>
  );
}
