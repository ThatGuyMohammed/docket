import { useEffect, useState } from "react";
import { api, type Doc, type User } from "../api";
import type { PublishedKey } from "../crypto/keystore";
import { sealV2 } from "../crypto/shareV2";

export default function ShareDialog({ doc, onClose }: { doc: Doc; onClose: () => void }) {
  const [people, setPeople] = useState<User[]>([]);
  const [recipient, setRecipient] = useState<number | null>(null);
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    api.directory().then((all) => setPeople(all.filter((u) => u.share_public_key)));
  }, []);

  async function share() {
    const person = people.find((p) => p.id === recipient);
    if (!person?.share_public_key) return;
    setStatus("Encrypting…");
    const key = JSON.parse(person.share_public_key) as PublishedKey;
    const content = await api.content(doc.id);
    const envelope = await sealV2(key.v2, content);
    await api.share(doc.id, person.id, envelope);
    setStatus(`Shared with ${person.display_name}`);
  }

  return (
    <div className="overlay" onClick={onClose}>
      <div className="card dialog" onClick={(e) => e.stopPropagation()}>
        <h3>Share “{doc.filename}”</h3>
        <p className="muted">Only the person you pick can open it. Docket's servers never see the contents.</p>
        <select value={recipient ?? ""} onChange={(e) => setRecipient(Number(e.target.value))}>
          <option value="" disabled>
            Choose a teammate
          </option>
          {people.map((p) => (
            <option key={p.id} value={p.id}>
              {p.display_name} ({p.email})
            </option>
          ))}
        </select>
        {status && <p>{status}</p>}
        <div className="actions">
          <button className="link" onClick={onClose}>
            Close
          </button>
          <button disabled={recipient === null} onClick={share}>
            Share
          </button>
        </div>
      </div>
    </div>
  );
}
