import { useEffect, useState } from "react";
import { api } from "../../api/client";

export default function Dashboard() {
  const [b, setB] = useState(null);
  useEffect(() => { api.get("/admin/billing").then(setB).catch(() => {}); }, []);
  return (
    <>
      <h2>Practice Dashboard</h2>
      {b && (
        <div className="grid2">
          <div className="card"><b style={{ fontSize: 28 }}>{b.doctor_count}</b><div className="muted">Doctors {b.max_doctors ? `/ ${b.max_doctors}` : "(unlimited)"}</div></div>
          <div className="card"><b style={{ fontSize: 28 }}>{b.patient_count}</b><div className="muted">Patients {b.max_patients ? `/ ${b.max_patients}` : "(unlimited)"}</div></div>
          <div className="card"><b style={{ fontSize: 20, textTransform: "capitalize" }}>{b.practice.subscription_tier}</b><div className="muted">Current plan</div></div>
          <div className="card"><b style={{ fontSize: 20 }}>{b.features.length}</b><div className="muted">Features enabled</div></div>
        </div>
      )}
    </>
  );
}
