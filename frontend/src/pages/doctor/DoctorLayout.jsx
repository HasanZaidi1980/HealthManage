import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";
import "../../styles/clinic.css";

export default function DoctorLayout() {
  const { user, logout } = useAuth();
  const nav = useNavigate();
  return (
    <div className="clinic">
      <div className="sidebar">
        <h1>HealthManage</h1>
        <NavLink end to="/doctor" className={({ isActive }) => (isActive ? "active" : "")}>Dashboard</NavLink>
        <NavLink to="/doctor/patients" className={({ isActive }) => (isActive ? "active" : "")}>Patient Search & Records</NavLink>
      </div>
      <div className="main">
        <div className="breadcrumb">
          <span>Dr. {user?.full_name} · Doctor Portal</span>
          <button className="btn ghost sm" onClick={() => { logout(); nav("/login"); }}>Sign out</button>
        </div>
        <div className="content"><Outlet /></div>
      </div>
    </div>
  );
}
