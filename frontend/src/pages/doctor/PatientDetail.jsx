import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../../api/client";
import Markdown from "../../components/Markdown";

const SECTIONS = [
  ["chief_conditions", "Chief Conditions"],
  ["current_medications", "Current Medications"],
  ["known_allergies", "Known Allergies"],
  ["recent_labs_imaging", "Recent Labs / Imaging"],
  ["recommended_followups", "Recommended Follow-Ups"],
];

export default function PatientDetail() {
  const { id } = useParams();
  const [patient, setPatient] = useState(null);
  const [meds, setMeds] = useState([]);
  const [flags, setFlags] = useState([]);
  const [summary, setSummary] = useState(null);
  const [share, setShare] = useState(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [med, setMed] = useState({ name_generic: "", name_brand: "", dosage: "", frequency: "", clinical_indication: "" });
  const [rec, setRec] = useState({ title: "", data: '{\n  "conditions": [],\n  "allergies": [],\n  "labs": []\n}' });
  const [conditions, setConditions] = useState([]);
  const [cx, setCx] = useState({ condition: "", level: "simple", text: "", busy: false });
  const cxCache = useRef({});
  const [appts, setAppts] = useState([]);
  const [clinicName, setClinicName] = useState("");
  const [newAppt, setNewAppt] = useState({ scheduled_at: "", purpose: "", location: "", telehealth_link: "" });
  const [completing, setCompleting] = useState(null);   // appt id being completed
  const [completeNotes, setCompleteNotes] = useState("");

  function loadMeds() {
    api.get(`/patients/${id}/medications`).then(setMeds).catch((e) => setErr(e.message));
    api.get(`/patients/${id}/medications/interactions`).then(setFlags).catch(() => {});
  }
  function loadSummary() {
    api.get(`/patients/${id}/health-summary`).then(setSummary).catch(() => setSummary(false));
  }
  useEffect(() => {
    api.get(`/patients/${id}`).then(setPatient).catch((e) => setErr(e.message));
    loadMeds(); loadSummary();
    api.get(`/patients/${id}/conditions`).then(setConditions).catch(() => {});
    loadAppts();
    api.get("/auth/me/practice").then((p) => {
      setClinicName(p.name);
      setNewAppt((s) => ({ ...s, location: s.location || p.name }));
    }).catch(() => {});
  }, [id]);

  function loadAppts() {
    api.get(`/patients/${id}/appointments`).then(setAppts).catch(() => {});
  }

  async function createAppt(e) {
    e.preventDefault(); setErr("");
    try {
      await api.post("/appointments", {
        patient_id: id,
        scheduled_at: new Date(newAppt.scheduled_at).toISOString(),
        purpose: newAppt.purpose,
        location: newAppt.location || null,
        telehealth_link: newAppt.telehealth_link || null,
      });
      setNewAppt({ scheduled_at: "", purpose: "", location: clinicName, telehealth_link: "" });
      loadAppts();
    } catch (e) { setErr(e.message); }
  }

  async function submitComplete(aid) {
    try {
      await api.patch(`/appointments/${aid}`, { status: "completed", notes: completeNotes });
      setCompleting(null); setCompleteNotes(""); loadAppts();
    } catch (e) { setErr(e.message); }
  }

  async function cancelAppt(aid) {
    try { await api.patch(`/appointments/${aid}`, { status: "cancelled" }); loadAppts(); }
    catch (e) { setErr(e.message); }
  }

  async function deleteAppt(aid) {
    if (!window.confirm("Delete this appointment permanently?")) return;
    try { await api.del(`/appointments/${aid}`); loadAppts(); }
    catch (e) { setErr(e.message); }
  }

  async function genApptChecklist(aid) {
    try { await api.post(`/appointments/${aid}/checklist`); loadAppts(); alert("Pre-visit checklist generated for the patient."); }
    catch (e) { setErr(e.message); }
  }

  async function explainCondition(condition, level) {
    const key = `${condition}|${level}`;
    if (cxCache.current[key] !== undefined) {  // reuse this session's fetch
      setCx({ condition, level, text: cxCache.current[key], busy: false });
      return;
    }
    setCx((s) => ({ ...s, condition, level, busy: true }));
    try {
      const r = await api.post(`/patients/${id}/conditions/explain`, { condition, level });
      cxCache.current[key] = r.explanation;
      setCx({ condition, level, text: r.explanation, busy: false });
    } catch (e) { setErr(e.message); setCx((s) => ({ ...s, busy: false })); }
  }

  async function addMed(e) {
    e.preventDefault(); setErr("");
    try {
      await api.post("/medications", { patient_id: id, ...med,
        name_brand: med.name_brand || null, clinical_indication: med.clinical_indication || null });
      setMed({ name_generic: "", name_brand: "", dosage: "", frequency: "", clinical_indication: "" });
      loadMeds();
    } catch (e) { setErr(e.message); }
  }

  async function uploadRecord(e) {
    e.preventDefault(); setErr("");
    try {
      const data = JSON.parse(rec.data);
      await api.post(`/patients/${id}/records`, { title: rec.title, source_type: "json", data });
      setRec({ ...rec, title: "" });
      alert("Record uploaded.");
    } catch (e) { setErr(/JSON/.test(e.message) ? "Invalid JSON in record data." : e.message); }
  }

  async function generate() {
    setErr(""); setBusy(true);
    try { setSummary(await api.post(`/patients/${id}/health-summary/generate`)); }
    catch (e) { setErr(e.message); }
    finally { setBusy(false); }
  }

  async function makeShare() {
    setErr("");
    try { setShare(await api.post(`/patients/${id}/health-summary/share`, { shared_with: "External provider", expires_in_days: 7 })); }
    catch (e) { setErr(e.message); }
  }

  async function downloadPdf() {
    try {
      const blob = await api.download(`/patients/${id}/health-summary/pdf`);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a"); a.href = url; a.download = "snapshot.pdf"; a.click();
      URL.revokeObjectURL(url);
    } catch (e) { setErr(e.message); }
  }

  return (
    <>
      <h2>{patient ? patient.full_name : "Patient"}</h2>
      {patient && <div className="muted" style={{ marginTop: -8, marginBottom: 16 }}>{patient.email}</div>}
      {err && <div className="error">{err}</div>}

      {/* Medications */}
      <h2>Medications</h2>
      {flags.length > 0 && (
        <div className="card" style={{ borderColor: "#c62828" }}>
          <b>⚠ Interaction flags</b>
          {flags.map((f, i) => (
            <div key={i} style={{ marginTop: 6 }}>
              {f.drug_a} + {f.drug_b} <span className={`badge ${f.severity}`}>{f.severity}</span>
              <div className="muted" style={{ fontSize: 13 }}>{f.note}</div>
            </div>
          ))}
        </div>
      )}
      <div className="card" style={{ padding: 0 }}>
        <table>
          <thead><tr><th>Drug</th><th>Dose</th><th>Indication</th></tr></thead>
          <tbody>
            {meds.map((m) => (
              <tr key={m.id}>
                <td>{m.name_generic}{m.name_brand ? ` (${m.name_brand})` : ""}</td>
                <td>{m.dosage} · {m.frequency}</td>
                <td className="muted">{m.clinical_indication ? <Markdown>{m.clinical_indication}</Markdown> : "—"}</td>
              </tr>
            ))}
            {meds.length === 0 && <tr><td colSpan={3} className="empty">No medications.</td></tr>}
          </tbody>
        </table>
      </div>
      <form className="card" onSubmit={addMed}>
        <b>Add medication</b>
        <div className="grid2" style={{ marginTop: 10 }}>
          <div className="field"><label>Generic name</label><input required value={med.name_generic} onChange={(e) => setMed({ ...med, name_generic: e.target.value })} /></div>
          <div className="field"><label>Brand (optional)</label><input value={med.name_brand} onChange={(e) => setMed({ ...med, name_brand: e.target.value })} /></div>
          <div className="field"><label>Dosage</label><input required value={med.dosage} onChange={(e) => setMed({ ...med, dosage: e.target.value })} /></div>
          <div className="field"><label>Frequency</label><input required value={med.frequency} onChange={(e) => setMed({ ...med, frequency: e.target.value })} /></div>
        </div>
        <div className="field"><label>Clinical indication (optional — AI fills if blank)</label><input value={med.clinical_indication} onChange={(e) => setMed({ ...med, clinical_indication: e.target.value })} /></div>
        <button className="btn">Add</button>
      </form>

      {/* Appointments */}
      <h2>Appointments</h2>
      <div className="card" style={{ padding: 0 }}>
        <table>
          <thead><tr><th>When</th><th>Purpose</th><th>Status</th><th></th></tr></thead>
          <tbody>
            {appts.map((a) => (
              <tr key={a.id}>
                <td>{new Date(a.scheduled_at).toLocaleString([], { dateStyle: "medium", timeStyle: "short" })}</td>
                <td>{a.purpose}{a.notes ? <div className="muted" style={{ fontSize: 12 }}>{a.notes}</div> : null}</td>
                <td><span className="badge low" style={{ background: a.status === "completed" ? "#9e9e9e" : a.status === "cancelled" ? "#c62828" : undefined }}>{a.status}</span></td>
                <td>
                  {a.status === "scheduled" ? (
                    completing === a.id ? (
                      <div style={{ minWidth: 220 }}>
                        <textarea rows={2} placeholder="Post-visit notes (optional)" style={{ width: "100%" }}
                          value={completeNotes} onChange={(e) => setCompleteNotes(e.target.value)} />
                        <div className="row" style={{ gap: 6, marginTop: 4 }}>
                          <button className="btn sm" onClick={() => submitComplete(a.id)}>Save & complete</button>
                          <button className="btn ghost sm" onClick={() => { setCompleting(null); setCompleteNotes(""); }}>Cancel</button>
                        </div>
                      </div>
                    ) : (
                      <div className="row" style={{ gap: 6, flexWrap: "wrap" }}>
                        <button className="btn ghost sm" onClick={() => genApptChecklist(a.id)}>
                          {a.has_checklist ? "Checklist ✓" : "Checklist"}
                        </button>
                        <button className="btn sm" onClick={() => { setCompleting(a.id); setCompleteNotes(""); }}>Complete</button>
                        <button className="btn ghost sm" onClick={() => cancelAppt(a.id)}>Cancel visit</button>
                        <button className="btn ghost sm" onClick={() => deleteAppt(a.id)}>Delete</button>
                      </div>
                    )
                  ) : (
                    <button className="btn ghost sm" onClick={() => deleteAppt(a.id)}>Delete</button>
                  )}
                </td>
              </tr>
            ))}
            {appts.length === 0 && <tr><td colSpan={4} className="empty">No appointments.</td></tr>}
          </tbody>
        </table>
      </div>
      <form className="card" onSubmit={createAppt}>
        <b>Schedule appointment</b>
        <div className="grid2" style={{ marginTop: 10 }}>
          <div className="field"><label>Date & time</label>
            <input type="datetime-local" required value={newAppt.scheduled_at}
              onChange={(e) => setNewAppt({ ...newAppt, scheduled_at: e.target.value })} /></div>
          <div className="field"><label>Purpose</label>
            <input required value={newAppt.purpose}
              onChange={(e) => setNewAppt({ ...newAppt, purpose: e.target.value })} /></div>
          <div className="field"><label>Location</label>
            <input value={newAppt.location}
              onChange={(e) => setNewAppt({ ...newAppt, location: e.target.value })} /></div>
          <div className="field"><label>Telehealth link (optional)</label>
            <input value={newAppt.telehealth_link}
              onChange={(e) => setNewAppt({ ...newAppt, telehealth_link: e.target.value })} /></div>
        </div>
        <button className="btn">Schedule</button>
      </form>

      {/* Condition Explainer */}
      <h2>Condition Explainer</h2>
      <div className="card">
        <p className="muted" style={{ marginTop: 0 }}>Generate a patient-ready explanation to share or print.</p>
        {conditions.length === 0 && <div className="empty">No conditions on file (upload a record below).</div>}
        <div className="row" style={{ flexWrap: "wrap", gap: 8 }}>
          {conditions.map((c) => (
            <button key={c.name} className="btn ghost sm" onClick={() => explainCondition(c.name, "simple")}>
              {c.name}
            </button>
          ))}
        </div>
        {cx.condition && (
          <div style={{ marginTop: 14 }}>
            <div className="row" style={{ gap: 8, marginBottom: 10, flexWrap: "wrap" }}>
              {["simple", "moderate", "detailed"].map((lvl) => (
                <button key={lvl}
                  className={`btn ${cx.level === lvl ? "" : "ghost"} sm`}
                  onClick={() => explainCondition(cx.condition, lvl)}>
                  {lvl[0].toUpperCase() + lvl.slice(1)}
                </button>
              ))}
              {cx.text && <button className="btn ghost sm" onClick={() => window.print()}>Print</button>}
            </div>
            <b>{cx.condition}</b>
            {cx.busy ? <p className="muted">Generating…</p>
              : <Markdown>{cx.text}</Markdown>}
          </div>
        )}
      </div>

      {/* Health Summary */}
      <h2>One-Page Snapshot</h2>
      <form className="card" onSubmit={uploadRecord}>
        <b>Upload source record (simulated EHR import — JSON)</b>
        <div className="field" style={{ marginTop: 10 }}><label>Title</label><input required value={rec.title} onChange={(e) => setRec({ ...rec, title: e.target.value })} /></div>
        <div className="field"><label>Structured data (JSON)</label>
          <textarea rows={6} style={{ width: "100%", fontFamily: "monospace" }} value={rec.data} onChange={(e) => setRec({ ...rec, data: e.target.value })} />
        </div>
        <button className="btn ghost">Upload Record</button>
      </form>

      <div className="card">
        <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
          <button className="btn" onClick={generate} disabled={busy}>{busy ? "Generating…" : "Generate / Refresh Snapshot"}</button>
          {summary && <button className="btn ghost" onClick={downloadPdf}>Download PDF</button>}
          {summary && <button className="btn ghost" onClick={makeShare}>Create Share Link</button>}
        </div>
        {summary === false && <p className="muted">No snapshot yet (generation requires the patient's AI-processing consent).</p>}
        {share && (
          <p className="muted" style={{ marginTop: 10 }}>
            Share link (expires {new Date(share.expires_at).toLocaleDateString()}):<br />
            <code>{share.share_url}</code>
          </p>
        )}
      </div>

      {summary && (
        <>
          <div className="card">
            <span className="badge low">Completeness {summary.completeness?.percent_complete}%</span>
            <span className="muted" style={{ marginLeft: 12, fontSize: 13 }}>
              Updated {new Date(summary.last_updated).toLocaleString()}
            </span>
          </div>
          {SECTIONS.map(([key, label]) => (
            <div className="card" key={key}>
              <b>{label}</b>
              {(summary.snapshot[key] || []).length === 0
                ? <div className="empty">None on file.</div>
                : <ul style={{ margin: "8px 0" }}>{summary.snapshot[key].map((it, i) => <li key={i}>{it}</li>)}</ul>}
            </div>
          ))}
          <div className="card muted" style={{ fontSize: 12 }}>{summary.snapshot.disclaimer}</div>
        </>
      )}
    </>
  );
}
