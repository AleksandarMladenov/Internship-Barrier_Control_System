import Sidebar from "../components/Sidebar/Sidebar";
import "./AdminLayout.css";

export default function AdminLayout({ title, actions, children }) {
  return (
    <div className="admin-wrap">
      <Sidebar />
      <main className="admin-main">
        <header className="admin-head">
          <h1>{title}</h1>
          <div>{actions}</div>
        </header>
        {children}
      </main>
    </div>
  );
}
