import { NavLink, useNavigate } from "react-router-dom";
import { FiTruck, FiLock, FiFileText, FiBarChart2, FiSettings, FiLogOut } from "react-icons/fi";
import { useAuth } from "../../hooks/useAuth";
import "./Sidebar.css";


export default function Sidebar() {
  const { logout, user } = useAuth();
  const navigate = useNavigate();

  async function onLogout() {
    await logout();
    navigate("/login", { replace: true });
  }

  return (
    <aside className="sb">
      <div className="sb-logo">
        <FiTruck size={22} />
        <span>Authorization</span>
      </div>

      <nav className="sb-nav">
        <NavLink to="/admins" className="sb-link">
          <FiLock /><span>Role Management</span>
        </NavLink>
        <NavLink to="/admin/authorization" className="sb-link">
          <FiTruck />
          <span>Authorization</span>
        </NavLink>
        <NavLink to="/reports" className="sb-link">
          <FiFileText /><span>Reports</span>
        </NavLink>
        <NavLink to="/analytics" className="sb-link">
          <FiBarChart2 /><span>Analytics</span>
        </NavLink>
        <NavLink to="/settings" className="sb-link">
          <FiSettings /><span>Settings</span>
        </NavLink>
      </nav>

      <div className="sb-footer">
        <div className="sb-user" title={user?.email}>{user?.email}</div>
        <button className="sb-logout" onClick={onLogout}>
          <FiLogOut /> <span>Logout</span>
        </button>
      </div>
    </aside>
  );
}
