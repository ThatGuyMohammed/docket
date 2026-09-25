import { useState, type FormEvent } from "react";
import { api, setToken, type User } from "../api";

export default function Login({ onLogin }: { onLogin: (u: User) => void }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const res = await api.login(email, password);
      setToken(res.access_token);
      onLogin(res.user);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <form className="card login" onSubmit={submit}>
      <h1>Docket</h1>
      <p className="muted">Sign, store and share documents with your team.</p>
      <label>
        Email
        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
      </label>
      <label>
        Password
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
      </label>
      {error && <p className="error">{error}</p>}
      <button type="submit">Sign in</button>
    </form>
  );
}
