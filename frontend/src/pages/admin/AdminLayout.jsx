import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";
import "../../styles/clinic.css";

export default function AdminLayout() {
  const { user, logout } = useAuth();
  const nav = useNavigate();
  return (
    <div className="clinic">
      <div className="sidebar">
        <h1>HealthManage</h1>
        <NavLink end to="/admin" className={({ isActive }) => (isActive ? "active" : "")}>Practice Dashboard</NavLink>
        <NavLink to="/admin/doctors" className={({ isActive }) => (isActive ? "active" : "")}>Manage Doctors</NavLink>
        <NavLink to="/admin/patients" className={({ isActive }) => (isActive ? "active" : "")}>Manage Patients</NavLink>
        <NavLink to="/admin/billing" className={({ isActive }) => (isActive ? "active" : "")}>Billing & Subscription</NavLink>
      </div>
      <div className="main">
        <div className="breadcrumb">
          <span>{user?.full_name} · Practice Admin</span>
          <button className="btn ghost sm" onClick={() => { logout(); nav("/login"); }}>Sign out</button>
        </div>
        <div className="content"><Outlet /></div>
      </div>
    </div>
  );
}
