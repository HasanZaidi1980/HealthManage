import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";
import "../../styles/patient.css";

const links = [
  ["", "Dashboard"],
  ["medications", "My Medications"],
  ["conditions", "My Conditions"],
  ["summary", "Health Summary"],
  ["consents", "Consent"],
];

export default function PatientLayout() {
  const { user, logout } = useAuth();
  const nav = useNavigate();
  return (
    <div className="patient">
      <div className="topbar">
        <h1>HealthManage</h1>
        <div className="row">
          <span className="muted" style={{ fontSize: 13 }}>{user?.full_name}</span>
          <button className="logout" onClick={() => { logout(); nav("/login"); }}>Sign out</button>
        </div>
      </div>
      <div className="nav">
        {links.map(([to, label]) => (
          <NavLink key={to} end={to === ""} to={`/patient/${to}`}
            className={({ isActive }) => (isActive ? "active" : "")}>{label}</NavLink>
        ))}
      </div>
      <div className="content"><Outlet /></div>
    </div>
  );
}
