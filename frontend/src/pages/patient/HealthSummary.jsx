import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client";

const SECTIONS = [
  ["chief_conditions", "Chief Conditions"],
  ["current_medications", "Current Medications"],
  ["known_allergies", "Known Allergies"],
  ["recent_labs_imaging", "Recent Labs / Imaging"],
  ["recommended_followups", "Recommended Follow-Ups"],
];

export default function HealthSummary() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  function load() {
    api.get("/me/health-summary").then(setData).catch((e) => {
      if (/404|No summary/i.test(e.message)) setData(false); else setErr(e.message);
    });
  }
  useEffect(load, []);

  async function generate() {
    setErr(""); setBusy(true);
    try { setData(await api.post("/me/health-summary/generate")); }
    catch (e) { setErr(e.message); }
    finally { setBusy(false); }
  }

  async function downloadPdf() {
    try {
      const blob = await api.download("/me/health-summary/pdf");
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = "health-snapshot.pdf"; a.click();
      URL.revokeObjectURL(url);
    } catch (e) { setErr(e.message); }
  }

  return (
    <>
      <h2>My Health Summary</h2>
      {err && <div className="error">{err}</div>}
      {data === false && (
        <div className="card">
          <div className="kv">No snapshot yet. Generating uses AI, which needs your consent first
            (<Link className="pill" to="/patient/consents">enable here</Link>).</div>
          <button className="btn" style={{ marginTop: 12 }} onClick={generate} disabled={busy}>
            {busy ? "Generating…" : "Generate Snapshot"}
          </button>
        </div>
      )}
      {data && (
        <>
          <div className="card">
            <div className="spread">
              <span className="pill">Completeness: {data.completeness?.percent_complete}%</span>
              <span className="muted" style={{ fontSize: 12 }}>
                Updated {new Date(data.last_updated).toLocaleString()}
              </span>
            </div>
            <div className="row" style={{ marginTop: 12, gap: 8 }}>
              <button className="btn" onClick={downloadPdf}>Download PDF</button>
              <button className="btn ghost" onClick={generate} disabled={busy}>{busy ? "…" : "Refresh"}</button>
            </div>
          </div>
          {SECTIONS.map(([key, label]) => (
            <div key={key}>
              <h2>{label}</h2>
              <div className="card">
                {(data.snapshot[key] || []).length === 0
                  ? <div className="empty">None on file.</div>
                  : data.snapshot[key].map((item, i) => <div className="kv" key={i}>• {item}</div>)}
              </div>
            </div>
          ))}
          {(data.completeness?.missing || []).length > 0 && (
            <>
              <h2>Data Gaps</h2>
              <div className="card">{data.completeness.missing.map((m, i) => <div className="kv" key={i}>• {m}</div>)}</div>
            </>
          )}
          <div className="card muted" style={{ fontSize: 12 }}>{data.snapshot.disclaimer}</div>
        </>
      )}
    </>
  );
}
