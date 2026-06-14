import { useEffect, useState } from "react";
import { api } from "../../api/client";

export default function Consents() {
  const [list, setList] = useState([]);
  const [err, setErr] = useState("");
  function load() { api.get("/me/consents").then(setList).catch((e) => setErr(e.message)); }
  useEffect(load, []);

  const latest = (type) => list.find((c) => c.consent_type === type);
  const aiOn = latest("ai_processing")?.granted;

  async function toggleAi(granted) {
    setErr("");
    try {
      await api.post("/me/consents", { consent_type: "ai_processing", version: "v1", granted });
      load();
    } catch (e) { setErr(e.message); }
  }

  return (
    <>
      <h2>Consent Management</h2>
      {err && <div className="error">{err}</div>}
      <div className="card">
        <div className="spread">
          <div>
            <div className="name">AI Processing</div>
            <div className="kv muted">Allows AI to summarize your records and check medication interactions.</div>
          </div>
          <span className="pill">{aiOn ? "Granted" : "Not granted"}</span>
        </div>
        <div className="row" style={{ marginTop: 12, gap: 8 }}>
          <button className="btn" onClick={() => toggleAi(true)} disabled={aiOn}>Grant</button>
          <button className="btn ghost" onClick={() => toggleAi(false)} disabled={!aiOn}>Revoke</button>
        </div>
      </div>
      <h2>History</h2>
      <div className="card">
        {list.length === 0 ? <div className="empty">No consent records.</div> :
          list.map((c) => (
            <div className="kv" key={c.id}>
              <b>{c.consent_type}</b> ({c.version}) — {c.granted ? "granted" : "revoked"} ·{" "}
              <span className="muted">{new Date(c.timestamp).toLocaleString()}</span>
            </div>
          ))}
      </div>
    </>
  );
}
