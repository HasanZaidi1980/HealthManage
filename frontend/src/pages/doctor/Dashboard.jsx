import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client";

export default function Dashboard() {
  const [patients, setPatients] = useState([]);
  useEffect(() => { api.get("/patients").then(setPatients).catch(() => {}); }, []);
  return (
    <>
      <h2>Dashboard</h2>
      <div className="card">
        <div className="spread">
          <b>{patients.length}</b><span className="muted">patients in your practice</span>
        </div>
      </div>
      <div className="card">
        <b>Quick access</b>
        <p className="muted">Open a patient to review medications, generate a One-Page Snapshot, and share it.</p>
        <Link className="btn" to="/doctor/patients">Go to Patients</Link>
      </div>
    </>
  );
}
