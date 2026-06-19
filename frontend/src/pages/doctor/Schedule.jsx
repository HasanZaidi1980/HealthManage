import { useEffect, useState } from "react";
import { api } from "../../api/client";

function fmt(dt) {
  return new Date(dt).toLocaleString([], { weekday: "short", month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
}

export default function Schedule() {
  const [range, setRange] = useState("week");
  const [appts, setAppts] = useState([]);
  const [err, setErr] = useState("");

  function load(r) {
    api.get(`/appointments?range=${r}`).then(setAppts).catch((e) => setErr(e.message));
  }
  useEffect(() => { load(range); }, [range]);

  // group by date
  const groups = {};
  appts.forEach((a) => {
    const key = new Date(a.scheduled_at).toLocaleDateString([], { weekday: "long", month: "long", day: "numeric" });
    (groups[key] = groups[key] || []).push(a);
  });

  return (
    <>
      <h2>My Schedule</h2>
      {err && <div className="error">{err}</div>}
      <div className="row" style={{ gap: 8, marginBottom: 12 }}>
        {["day", "week", "all"].map((r) => (
          <button key={r} className={`btn ${range === r ? "" : "ghost"} sm`} onClick={() => setRange(r)}>
            {r[0].toUpperCase() + r.slice(1)}
          </button>
        ))}
      </div>
      {appts.length === 0 && <div className="empty">No appointments in this range.</div>}
      {Object.entries(groups).map(([day, list]) => (
        <div className="card" key={day}>
          <b>{day}</b>
          <table style={{ marginTop: 8, tableLayout: "fixed", width: "100%" }}>
            <colgroup>
              <col style={{ width: "90px" }} />
              <col style={{ width: "45%" }} />
              <col style={{ width: "35%" }} />
              <col style={{ width: "110px" }} />
            </colgroup>
            <tbody>
              {list.map((a) => (
                <tr key={a.id}>
                  <td>{new Date(a.scheduled_at).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}</td>
                  <td>{a.purpose}</td>
                  <td className="muted">{a.location || (a.telehealth_link ? "Telehealth" : "—")}</td>
                  <td><span className="badge low" style={{ background: a.status === "completed" ? "#9e9e9e" : a.status === "cancelled" ? "#c62828" : undefined }}>{a.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </>
  );
}
