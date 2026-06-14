import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client";
import { useAuth } from "../../auth/AuthContext";

export default function Dashboard() {
  const { user } = useAuth();
  const [meds, setMeds] = useState([]);
  useEffect(() => { api.get("/me/medications").then(setMeds).catch(() => {}); }, []);
  return (
    <>
      <h2>Welcome, {user?.full_name?.split(" ")[0]}</h2>
      <div className="card">
        <div className="name">Your health snapshot</div>
        <div className="kv muted">A One-Page Snapshot summarizes your conditions, medications, allergies and labs.</div>
        <div style={{ marginTop: 12 }}><Link className="btn ghost" to="/patient/summary">View Health Summary</Link></div>
      </div>
      <div className="card">
        <div className="spread">
          <div className="name">Active medications</div>
          <span className="pill">{meds.length}</span>
        </div>
        <div className="kv muted">{meds.slice(0, 3).map((m) => m.name_generic).join(", ") || "None yet"}</div>
        <div style={{ marginTop: 12 }}><Link className="btn ghost" to="/patient/medications">View Medications</Link></div>
      </div>
    </>
  );
}
