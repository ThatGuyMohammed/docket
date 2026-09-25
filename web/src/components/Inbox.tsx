import { useEffect, useState } from "react";
import { api, type Share, type User } from "../api";
import type { Identity } from "../crypto/keystore";
import { openV1 } from "../crypto/shareV1";
import { openV2 } from "../crypto/shareV2";

async function openShare(identity: Identity, s: Share): Promise<Uint8Array> {
  if (s.version === 1) return openV1(identity.v1.privateJwk, s.envelope_b64);
  return openV2(identity.v2.secretKey, s.envelope_b64);
}

export default function Inbox({ me, identity }: { me: User; identity: Identity }) {
  const [shares, setShares] = useState<Share[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.shares().then((all) => setShares(all.filter((s) => s.recipient_id === me.id)));
  }, [me.id]);

  async function download(s: Share) {
    setError(null);
    try {
      const bytes = await openShare(identity, s);
      const url = URL.createObjectURL(new Blob([new Uint8Array(bytes)]));
      const a = document.createElement("a");
      a.href = url;
      a.download = `shared-${s.document_id}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setError("This share could not be opened on this device.");
    }
  }

  return (
    <section>
      <h2>Shared with me</h2>
      {error && <p className="error">{error}</p>}
      <ul className="list">
        {shares.map((s) => (
          <li key={s.id}>
            <span>Document #{s.document_id}</span>
            <span className="muted">{s.created_at ? new Date(s.created_at).toLocaleString() : ""}</span>
            <button onClick={() => download(s)}>Open</button>
          </li>
        ))}
        {shares.length === 0 && <li className="muted">No one has shared anything with you yet.</li>}
      </ul>
    </section>
  );
}
