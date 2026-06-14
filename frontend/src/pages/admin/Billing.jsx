import { useEffect, useState } from "react";
import { api } from "../../api/client";

export default function Billing() {
  const [b, setB] = useState(null);
  useEffect(() => { api.get("/admin/billing").then(setB).catch(() => {}); }, []);
  if (!b) return <h2>Billing & Subscription</h2>;
  return (
    <>
      <h2>Billing & Subscription</h2>
      <div className="card">
        <div className="spread">
          <div><b style={{ fontSize: 22, textTransform: "capitalize" }}>{b.practice.subscription_tier} plan</b>
            <div className="muted">{b.practice.name}</div></div>
          <span className="badge low">Active</span>
        </div>
      </div>
      <div className="card">
        <b>Included features</b>
        <ul>{b.features.map((f) => <li key={f} style={{ textTransform: "capitalize" }}>{f.replace(/_/g, " ")}</li>)}</ul>
      </div>
      <div className="card">
        <b>Seat usage</b>
        <p>Doctors: {b.doctor_count}{b.max_doctors ? ` / ${b.max_doctors}` : " (unlimited)"}</p>
        <p>Patients: {b.patient_count}{b.max_patients ? ` / ${b.max_patients}` : " (unlimited)"}</p>
      </div>
    </>
  );
}
