import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client";
import Markdown from "../../components/Markdown";

export default function Medications() {
  const [meds, setMeds] = useState([]);
  const [flags, setFlags] = useState([]);
  const [needConsent, setNeedConsent] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    api.get("/me/medications").then(setMeds).catch((e) => setErr(e.message));
    api.get("/me/medications/interactions")
      .then(setFlags)
      .catch((e) => { if (/consent/i.test(e.message)) setNeedConsent(true); });
  }, []);

  const inInteraction = (name) =>
    flags.find((f) => [f.drug_a, f.drug_b].includes(name.toLowerCase()));

  return (
    <>
      <h2>My Medications</h2>
      {err && <div className="error">{err}</div>}
      {needConsent && (
        <div className="card">
          <div className="kv">Enable AI interaction checks under <Link className="pill" to="/patient/consents">Consent</Link>.</div>
        </div>
      )}
      {flags.length > 0 && (
        <div className="card" style={{ borderColor: "#c62828" }}>
          <div className="name">⚠ Possible interactions</div>
          {flags.map((f, i) => (
            <div className="kv" key={i}>
              <b>{f.drug_a} + {f.drug_b}</b> <span className={`badge ${f.severity}`}>{f.severity}</span><br />
              <span className="muted">{f.note}</span>
            </div>
          ))}
        </div>
      )}
      {meds.length === 0 && <div className="empty">No medications on file.</div>}
      {meds.map((m) => (
        <div className="card" key={m.id}>
          <div className="spread">
            <div className="name">{m.name_generic}{m.name_brand ? ` (${m.name_brand})` : ""}</div>
            {inInteraction(m.name_generic) && <span className="badge high">interaction</span>}
          </div>
          <div className="kv"><b>Dose:</b> {m.dosage} · {m.frequency}</div>
          <div className="kv"><b>Prescriber:</b> {m.prescribing_provider || "—"}</div>
          {m.plain_language_purpose && <div className="kv muted"><Markdown>{m.plain_language_purpose}</Markdown></div>}
        </div>
      ))}
    </>
  );
}
