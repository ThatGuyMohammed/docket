// Sharing keys live in the browser only. The public halves are published to
// the server so teammates can share with us.
import { generateV1KeyPair } from "./shareV1";
import { generateV2Keys, type V2PublicKey, type V2SecretKey } from "./shareV2";

export type Identity = {
  v2: { publicKey: V2PublicKey; secretKey: V2SecretKey };
  v1: { publicJwk: JsonWebKey; privateJwk: JsonWebKey };
};

export type PublishedKey = { v2: V2PublicKey; v1: JsonWebKey };

const STORAGE_KEY = "docket.identity";

export async function loadOrCreateIdentity(): Promise<{ identity: Identity; created: boolean }> {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved) return { identity: JSON.parse(saved), created: false };
  const identity: Identity = { v2: generateV2Keys(), v1: await generateV1KeyPair() };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(identity));
  return { identity, created: true };
}

export function publishedKey(id: Identity): string {
  const pk: PublishedKey = { v2: id.v2.publicKey, v1: id.v1.publicJwk };
  return JSON.stringify(pk);
}
