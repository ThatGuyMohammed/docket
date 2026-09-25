import { useEffect, useState } from "react";
import { api, hasToken, setToken, type User } from "./api";
import { loadOrCreateIdentity, publishedKey, type Identity } from "./crypto/keystore";
import Login from "./components/Login";
import Documents from "./components/Documents";
import Inbox from "./components/Inbox";

type Tab = "documents" | "inbox";

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [identity, setIdentity] = useState<Identity | null>(null);
  const [tab, setTab] = useState<Tab>("documents");

  useEffect(() => {
    if (hasToken()) api.me().then(setUser).catch(() => setUser(null));
  }, []);

  useEffect(() => {
    if (!user) return;
    loadOrCreateIdentity().then(({ identity, created }) => {
      setIdentity(identity);
      if (created || !user.share_public_key) api.setShareKey(publishedKey(identity));
    });
  }, [user]);

  if (!user) return <Login onLogin={setUser} />;

  return (
    <div className="shell">
      <header>
        <strong>Docket</strong>
        <nav>
          <button className={tab === "documents" ? "active" : ""} onClick={() => setTab("documents")}>
            Documents
          </button>
          <button className={tab === "inbox" ? "active" : ""} onClick={() => setTab("inbox")}>
            Shared with me
          </button>
        </nav>
        <span className="muted">{user.display_name}</span>
        <button
          className="link"
          onClick={() => {
            setToken(null);
            setUser(null);
          }}
        >
          Sign out
        </button>
      </header>
      <main>
        {tab === "documents" && <Documents />}
        {tab === "inbox" && identity && <Inbox me={user} identity={identity} />}
      </main>
    </div>
  );
}
