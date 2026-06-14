import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../../api/client";

export default function Patients() {
  const [patients, setPatients] = useState([]);
  const [q, setQ] = useState("");
  const nav = useNavigate();
  useEffect(() => { api.get("/patients").then(setPatients).catch(() => {}); }, []);
  const filtered = patients.filter((p) =>
    (p.full_name + p.email).toLowerCase().includes(q.toLowerCase()));
  return (
    <>
      <h2>Patient Search & Records</h2>
      <div className="field" style={{ maxWidth: 360 }}>
        <input placeholder="Search by name or email…" value={q} onChange={(e) => setQ(e.target.value)} />
      </div>
      <div className="card" style={{ padding: 0 }}>
        <table>
          <thead><tr><th>Name</th><th>Email</th><th></th></tr></thead>
          <tbody>
            {filtered.map((p) => (
              <tr key={p.id}>
                <td>{p.full_name}</td>
                <td className="muted">{p.email}</td>
                <td><button className="btn sm" onClick={() => nav(`/doctor/patients/${p.id}`)}>Open</button></td>
              </tr>
            ))}
            {filtered.length === 0 && <tr><td colSpan={3} className="empty">No patients.</td></tr>}
          </tbody>
        </table>
      </div>
    </>
  );
}
