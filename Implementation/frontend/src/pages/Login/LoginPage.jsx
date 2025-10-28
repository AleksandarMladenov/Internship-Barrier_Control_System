import "./Login.css";
import LoginForm from "./LoginForm";
import { useAuth } from "../../hooks/useAuth";
import { Navigate } from "react-router-dom";

export default function LoginPage() {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (user) return <Navigate to="/admins" replace />;

  return (
    <div className="login-wrap">
      <div className="login-left">
        <h1>Petroff Parking</h1>
      </div>
      <div className="login-right">
        <h2>Login</h2>
        <LoginForm />
      </div>
    </div>
  );
}
