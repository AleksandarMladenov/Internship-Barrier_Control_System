import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import LoginPage from "../pages/Login/LoginPage";
import AcceptInvitePage from "../pages/AcceptInvite/AcceptInvitePage";
import RoleManagementPage from "../pages/RoleManagement/RoleManagementPage";
import ProtectedRoute from "./ProtectedRoute";

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/accept-invite" element={<AcceptInvitePage />} />

        <Route element={<ProtectedRoute />}>
          <Route path="/admins" element={<RoleManagementPage />} />
          {/* stubs for the left-rail links so the nav highlights correctly */}
          <Route path="/reports" element={<Navigate to="/admins" replace />} />
          <Route path="/analytics" element={<Navigate to="/admins" replace />} />
          <Route path="/settings" element={<Navigate to="/admins" replace />} />
        </Route>

        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
