import { useEffect, useState } from "react";
import { api } from "../api/client";

export default function ManageUsers({ role, createPath, title }) {
  const [users, setUsers] = useState([]);
  const [form, setForm] = useState({ email: "", password: "", full_name: "" });
  const [err, setErr] = useState("");

  function load() { api.get("/admin/users").then((all) => setUsers(all.filter((u) => u.role === role))).catch((e) => setErr(e.message)); }
  useEffect(load, [role]);

  async function add(e) {
    e.preventDefault(); setErr("");
    try { await api.post(createPath, form); setForm({ email: "", password: "", full_name: "" }); load(); }
    catch (e) { setErr(e.message); }
  }
  async function deactivate(uid) {
    setErr("");
    try { await api.patch(`/admin/users/${uid}/deactivate`); load(); }
    catch (e) { setErr(e.message); }
  }

  return (
    <>
      <h2>{title}</h2>
      {err && <div className="error">{err}</div>}
      <div className="card" style={{ padding: 0 }}>
        <table>
          <thead><tr><th>Name</th><th>Email</th><th>Status</th><th></th></tr></thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td>{u.full_name}</td>
                <td className="muted">{u.email}</td>
                <td>{u.is_active ? "Active" : "Deactivated"}</td>
                <td>{u.is_active && <button className="btn ghost sm" onClick={() => deactivate(u.id)}>Deactivate</button>}</td>
              </tr>
            ))}
            {users.length === 0 && <tr><td colSpan={4} className="empty">None yet.</td></tr>}
          </tbody>
        </table>
      </div>
      <form className="card" onSubmit={add}>
        <b>Add {role}</b>
        <div className="grid2" style={{ marginTop: 10 }}>
          <div className="field"><label>Full name</label><input required value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} /></div>
          <div className="field"><label>Email</label><input type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></div>
        </div>
        <div className="field"><label>Temporary password (min 8 chars)</label><input type="password" required minLength={8} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} /></div>
        <button className="btn">Create account</button>
      </form>
    </>
  );
}
