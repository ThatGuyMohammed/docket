import { useEffect, useState } from "react";
import { api, type Doc } from "../api";
import ShareDialog from "./ShareDialog";

function formatSize(n: number) {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
}

export default function Documents() {
  const [docs, setDocs] = useState<Doc[]>([]);
  const [sharing, setSharing] = useState<Doc | null>(null);
  const [busy, setBusy] = useState(false);

  const refresh = () => api.documents().then(setDocs);
  useEffect(() => {
    refresh();
  }, []);

  async function onUpload(files: FileList | null) {
    if (!files?.length) return;
    setBusy(true);
    try {
      for (const f of Array.from(files)) await api.upload(f);
      await refresh();
    } finally {
      setBusy(false);
    }
  }

  return (
    <section>
      <div className="toolbar">
        <h2>Your documents</h2>
        <label className="button">
          {busy ? "Uploading…" : "Upload"}
          <input type="file" multiple hidden onChange={(e) => onUpload(e.target.files)} />
        </label>
      </div>
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Size</th>
            <th>Status</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {docs.map((d) => (
            <tr key={d.id}>
              <td>{d.filename}</td>
              <td>{formatSize(d.size_bytes)}</td>
              <td>{d.signed ? <span className="badge ok">Signed</span> : <span className="badge">Draft</span>}</td>
              <td className="actions">
                {!d.signed && <button onClick={() => api.sign(d.id).then(refresh)}>Sign</button>}
                <button onClick={() => setSharing(d)}>Share</button>
              </td>
            </tr>
          ))}
          {docs.length === 0 && (
            <tr>
              <td colSpan={4} className="muted">
                Nothing here yet. Upload a document to get started.
              </td>
            </tr>
          )}
        </tbody>
      </table>
      {sharing && <ShareDialog doc={sharing} onClose={() => setSharing(null)} />}
    </section>
  );
}
