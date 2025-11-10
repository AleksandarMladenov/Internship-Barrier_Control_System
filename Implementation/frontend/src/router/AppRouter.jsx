
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import LoginPage from "../pages/Login/LoginPage";
import AcceptInvitePage from "../pages/AcceptInvite/AcceptInvitePage";
import RoleManagementPage from "../pages/RoleManagement/RoleManagementPage";
import ProtectedRoute from "./ProtectedRoute";
import SubscriptionPage from "../pages/Subscribe/SubscriptionPage";
import AuthorizationPage from "../pages/Authorization/AuthorizationPage";


export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/accept-invite" element={<AcceptInvitePage />} />
        <Route path="/subscribe" element={<SubscriptionPage />} />

        <Route element={<ProtectedRoute />}>
          <Route path="/admins" element={<RoleManagementPage />} />

          <Route path="/admin/authorization" element={<AuthorizationPage />} />

          <Route path="/reports" element={<Navigate to="/admins" replace />} />
          <Route path="/analytics" element={<Navigate to="/admins" replace />} />
          <Route path="/settings" element={<Navigate to="/admins" replace />} />
        </Route>

        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
