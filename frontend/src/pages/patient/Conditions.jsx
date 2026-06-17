import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client";

const LEVELS = [
  ["simple", "Simple"],
  ["moderate", "Moderate"],
  ["detailed", "Detailed"],
];

export default function Conditions() {
  const [conditions, setConditions] = useState([]);
  const [selected, setSelected] = useState(null);
  const [level, setLevel] = useState("simple");
  const [explanation, setExplanation] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [needConsent, setNeedConsent] = useState(false);

  useEffect(() => {
    api.get("/me/conditions").then(setConditions).catch((e) => setErr(e.message));
  }, []);

  async function explain(condition, lvl) {
    setBusy(true); setErr(""); setNeedConsent(false);
    try {
      const r = await api.post("/me/conditions/explain", { condition, level: lvl });
      setExplanation(r.explanation);
    } catch (e) {
      if (/consent/i.test(e.message)) setNeedConsent(true);
      else setErr(e.message);
      setExplanation("");
    } finally {
      setBusy(false);
    }
  }

  function pick(name) {
    setSelected(name);
    setLevel("simple");
    explain(name, "simple");
  }

  function changeLevel(lvl) {
    setLevel(lvl);
    if (selected) explain(selected, lvl);
  }

  return (
    <>
      <h2>My Conditions</h2>
      {err && <div className="error">{err}</div>}
      {conditions.length === 0 && (
        <div className="empty">No conditions on file yet. They appear once your records are uploaded.</div>
      )}

      {conditions.map((c) => (
        <div className="card" key={c.name}>
          <div className="spread">
            <div>
              <div className="name">{c.name}</div>
              {c.status && <div className="kv muted">{c.status}</div>}
            </div>
            <button className="btn ghost" onClick={() => pick(c.name)}>Explain</button>
          </div>
        </div>
      ))}

      {needConsent && (
        <div className="card">
          <div className="kv">AI explanations need your consent —
            <Link className="pill" to="/patient/consents"> enable here</Link>.</div>
        </div>
      )}

      {selected && !needConsent && (
        <>
          <h2>About: {selected}</h2>
          <div className="card">
            <div className="row" style={{ gap: 8, marginBottom: 12, flexWrap: "wrap" }}>
              {LEVELS.map(([val, label]) => (
                <button key={val}
                  className={`btn ${level === val ? "" : "ghost"}`}
                  onClick={() => changeLevel(val)}>{label}</button>
              ))}
            </div>
            {busy ? <div className="kv muted">Generating…</div>
              : <div className="kv" style={{ whiteSpace: "pre-line", lineHeight: 1.6 }}>{explanation}</div>}
          </div>
        </>
      )}
    </>
  );
}
