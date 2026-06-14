import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import "../styles/login.css";

export default function Login() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setErr(""); setBusy(true);
    try {
      const me = await login(email.trim(), password);
      nav(`/${me.role}`, { replace: true });
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-wrap">
      <form className="login-card" onSubmit={submit}>
        <h1>HealthManage</h1>
        <p>Sign in — you'll be routed to your portal.</p>
        <div className="field">
          <label>Email</label>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </div>
        <div className="field">
          <label>Password</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </div>
        {err && <div className="error">{err}</div>}
        <button disabled={busy}>{busy ? "Signing in…" : "Sign In"}</button>
        <div className="hint">
          Seeded demo logins (password: password123):<br />
          admin@katyclinic.example.com<br />
          dr.reyes@katyclinic.example.com<br />
          patient.jordan@katyclinic.example.com
        </div>
      </form>
    </div>
  );
}
