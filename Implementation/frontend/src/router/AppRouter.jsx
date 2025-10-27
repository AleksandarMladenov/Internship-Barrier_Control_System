import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import LoginPage from "../pages/Login/LoginPage";

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        {/* for now, everything redirects to /login */}
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
