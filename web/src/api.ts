export type User = { id: number; email: string; display_name: string; share_public_key: string | null };
export type Doc = {
  id: number;
  filename: string;
  size_bytes: number;
  sha256: string;
  signed: boolean;
  signature_alg: string | null;
  signed_at: string | null;
};
export type Share = {
  id: number;
  document_id: number;
  sender_id: number;
  recipient_id: number;
  version: number;
  envelope_b64: string;
  created_at: string | null;
};

let token: string | null = localStorage.getItem("docket.token");

export function setToken(t: string | null) {
  token = t;
  if (t) localStorage.setItem("docket.token", t);
  else localStorage.removeItem("docket.token");
}

export function hasToken() {
  return token !== null;
}

async function call<T>(method: string, path: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  let payload: BodyInit | undefined;
  if (body instanceof FormData) payload = body;
  else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }
  const res = await fetch(path, { method, headers, body: payload });
  if (res.status === 401) setToken(null);
  if (!res.ok) throw new Error((await res.json().catch(() => null))?.detail ?? res.statusText);
  return res.status === 204 ? (undefined as T) : res.json();
}

export const api = {
  login: (email: string, password: string) =>
    call<{ access_token: string; user: User }>("POST", "/api/accounts/login", { email, password }),
  me: () => call<User>("GET", "/api/accounts/me"),
  directory: () => call<User[]>("GET", "/api/accounts/directory"),
  setShareKey: (public_key: string) => call<User>("PUT", "/api/accounts/me/share-key", { public_key }),
  documents: () => call<Doc[]>("GET", "/api/documents"),
  upload: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return call<Doc>("POST", "/api/documents", fd);
  },
  sign: (id: number) => call<Doc>("POST", `/api/documents/${id}/sign`),
  content: async (id: number) => {
    const res = await fetch(`/api/documents/${id}/content`, { headers: { Authorization: `Bearer ${token}` } });
    return new Uint8Array(await res.arrayBuffer());
  },
  shares: () => call<Share[]>("GET", "/api/shares"),
  share: (document_id: number, recipient_id: number, envelope_b64: string) =>
    call<Share>("POST", "/api/shares", { document_id, recipient_id, version: 2, envelope_b64 }),
};
