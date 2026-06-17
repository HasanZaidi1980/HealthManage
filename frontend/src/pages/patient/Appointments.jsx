import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client";

function fmt(dt) {
  return new Date(dt).toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
}

function MiniCalendar({ appts }) {
  const [base, setBase] = useState(() => { const d = new Date(); d.setDate(1); return d; });
  const year = base.getFullYear(), month = base.getMonth();
  const first = new Date(year, month, 1).getDay();
  const days = new Date(year, month + 1, 0).getDate();
  const apptDays = new Set(
    appts.filter((a) => { const d = new Date(a.scheduled_at); return d.getFullYear() === year && d.getMonth() === month; })
         .map((a) => new Date(a.scheduled_at).getDate())
  );
  const cells = [];
  for (let i = 0; i < first; i++) cells.push(null);
  for (let d = 1; d <= days; d++) cells.push(d);
  const today = new Date();
  const isToday = (d) => d === today.getDate() && month === today.getMonth() && year === today.getFullYear();

  return (
    <div className="card">
      <div className="spread" style={{ marginBottom: 8 }}>
        <button className="btn ghost" onClick={() => setBase(new Date(year, month - 1, 1))}>‹</button>
        <b>{base.toLocaleString([], { month: "long", year: "numeric" })}</b>
        <button className="btn ghost" onClick={() => setBase(new Date(year, month + 1, 1))}>›</button>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(7,1fr)", gap: 4, textAlign: "center" }}>
        {["S", "M", "T", "W", "T", "F", "S"].map((d, i) => <div key={i} className="muted" style={{ fontSize: 12 }}>{d}</div>)}
        {cells.map((d, i) => (
          <div key={i} style={{
            padding: "6px 0", borderRadius: 8, fontSize: 13,
            background: d && apptDays.has(d) ? "var(--accent)" : "transparent",
            color: d && apptDays.has(d) ? "#fff" : "inherit",
            outline: d && isToday(d) ? "1px solid var(--accent)" : "none",
          }}>{d || ""}</div>
        ))}
      </div>
    </div>
  );
}

function Checklist({ apptId, onErr }) {
  const [cl, setCl] = useState(null);
  const [busy, setBusy] = useState(false);
  const [needConsent, setNeedConsent] = useState(false);

  useEffect(() => {
    api.get(`/me/appointments/${apptId}/checklist`).then(setCl).catch(() => {});
  }, [apptId]);

  async function gen() {
    setBusy(true); setNeedConsent(false);
    try { setCl(await api.post(`/me/appointments/${apptId}/checklist`)); }
    catch (e) { if (/consent/i.test(e.message)) setNeedConsent(true); else onErr(e.message); }
    finally { setBusy(false); }
  }

  if (needConsent) return (
    <div className="kv">Pre-visit checklist needs AI consent —
      <Link className="pill" to="/patient/consents"> enable here</Link>.</div>
  );
  if (!cl) return <button className="btn ghost" onClick={gen} disabled={busy}>{busy ? "Generating…" : "Generate pre-visit checklist"}</button>;

  const Section = ({ title, items }) => items?.length ? (
    <div style={{ marginTop: 8 }}>
      <b>{title}</b>
      <ul style={{ margin: "4px 0" }}>{items.map((x, i) => <li key={i}>{x}</li>)}</ul>
    </div>
  ) : null;

  return (
    <div style={{ marginTop: 8 }}>
      <Section title="Questions to ask" items={cl.questions} />
      <Section title="Documents to bring" items={cl.documents} />
      <Section title="Medications to mention" items={cl.medications_to_mention} />
      <button className="btn ghost" onClick={gen} disabled={busy} style={{ marginTop: 6 }}>{busy ? "…" : "Refresh"}</button>
    </div>
  );
}

export default function Appointments() {
  const [appts, setAppts] = useState([]);
  const [reminders, setReminders] = useState([]);
  const [open, setOpen] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api.get("/me/appointments").then(setAppts).catch((e) => setErr(e.message));
    api.get("/me/appointments/reminders").then(setReminders).catch(() => {});
  }, []);

  const now = new Date();
  const upcoming = appts.filter((a) => a.status === "scheduled" && new Date(a.scheduled_at) >= now);
  const past = appts.filter((a) => a.status !== "scheduled" || new Date(a.scheduled_at) < now);

  const Card = ({ a }) => (
    <div className="card">
      <div className="spread">
        <div className="name">{a.purpose}</div>
        <span className="pill">{a.status}</span>
      </div>
      <div className="kv"><b>When:</b> {fmt(a.scheduled_at)}</div>
      <div className="kv"><b>Provider:</b> {a.provider_name || "—"}</div>
      <div className="kv"><b>Where:</b> {a.location || "—"}
        {a.telehealth_link && <> · <a className="pill" href={a.telehealth_link} target="_blank" rel="noreferrer">Join telehealth</a></>}
      </div>
      {a.notes && <div className="kv"><b>Visit notes:</b> {a.notes}</div>}
      {a.status === "scheduled" && (
        <div style={{ marginTop: 10 }}>
          {open === a.id
            ? <Checklist apptId={a.id} onErr={setErr} />
            : <button className="btn ghost" onClick={() => setOpen(a.id)}>Pre-visit checklist</button>}
        </div>
      )}
    </div>
  );

  return (
    <>
      <h2>Appointments</h2>
      {err && <div className="error">{err}</div>}
      {reminders.length > 0 && (
        <div className="card" style={{ borderColor: "var(--accent)" }}>
          <div className="name">🔔 Reminders</div>
          {reminders.map((r) => <div className="kv" key={r.appointment_id}>{r.message}</div>)}
        </div>
      )}

      <MiniCalendar appts={appts} />

      <h2>Upcoming</h2>
      {upcoming.length === 0 ? <div className="empty">No upcoming appointments.</div>
        : upcoming.map((a) => <Card key={a.id} a={a} />)}

      <h2>Past</h2>
      {past.length === 0 ? <div className="empty">No past appointments.</div>
        : past.map((a) => <Card key={a.id} a={a} />)}
    </>
  );
}
