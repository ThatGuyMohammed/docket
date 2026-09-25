// Share format v1 (Docket 0.2 and earlier). New shares are always v2; this is
// kept so people can still open documents shared before the upgrade, and so
// the 0.2 desktop client can keep sending to us until it is retired.
import { fromB64, toB64 } from "./encoding";

type V1Envelope = { v: 1; epk: JsonWebKey; iv: string; data: string };

export async function generateV1KeyPair(): Promise<{ publicJwk: JsonWebKey; privateJwk: JsonWebKey }> {
  const pair = await crypto.subtle.generateKey({ name: "ECDH", namedCurve: "P-256" }, true, ["deriveKey"]);
  return {
    publicJwk: await crypto.subtle.exportKey("jwk", pair.publicKey),
    privateJwk: await crypto.subtle.exportKey("jwk", pair.privateKey),
  };
}

async function derive(privateKey: CryptoKey, publicKey: CryptoKey) {
  return crypto.subtle.deriveKey(
    { name: "ECDH", public: publicKey },
    privateKey,
    { name: "AES-GCM", length: 256 },
    false,
    ["encrypt", "decrypt"],
  );
}

export async function openV1(privateJwk: JsonWebKey, envelopeB64: string): Promise<Uint8Array> {
  const env = JSON.parse(atob(envelopeB64)) as V1Envelope;
  if (env.v !== 1) throw new Error("not a v1 share");
  const alg = { name: "ECDH", namedCurve: "P-256" };
  const priv = await crypto.subtle.importKey("jwk", privateJwk, alg, false, ["deriveKey"]);
  const pub = await crypto.subtle.importKey("jwk", env.epk, alg, false, []);
  const key = await derive(priv, pub);
  const out = await crypto.subtle.decrypt({ name: "AES-GCM", iv: fromB64(env.iv) }, key, fromB64(env.data));
  return new Uint8Array(out);
}

// Only used by tests to produce shares in the old format.
export async function sealV1(recipientJwk: JsonWebKey, plaintext: Uint8Array<ArrayBuffer>): Promise<string> {
  const eph = await generateV1KeyPair();
  const alg = { name: "ECDH", namedCurve: "P-256" };
  const priv = await crypto.subtle.importKey("jwk", eph.privateJwk, alg, false, ["deriveKey"]);
  const pub = await crypto.subtle.importKey("jwk", recipientJwk, alg, false, []);
  const key = await derive(priv, pub);
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const data = new Uint8Array(await crypto.subtle.encrypt({ name: "AES-GCM", iv }, key, plaintext));
  const env: V1Envelope = { v: 1, epk: eph.publicJwk, iv: toB64(iv), data: toB64(data) };
  return btoa(JSON.stringify(env));
}
