// Share format v2: the file key is derived from both an ML-KEM-768
// encapsulation and an X25519 exchange, then used for AES-GCM.
import { ml_kem768 } from "@noble/post-quantum/ml-kem.js";
import { x25519 } from "@noble/curves/ed25519.js";
import { hkdf } from "@noble/hashes/hkdf.js";
import { sha256 } from "@noble/hashes/sha2.js";
import { fromB64, toB64, utf8 } from "./encoding";

export type V2PublicKey = { kem: string; x: string };
export type V2SecretKey = { kem: string; x: string };

type Envelope = { v: 2; ct: string; epk: string; iv: string; data: string };

const INFO = utf8.encode("docket share v2");

export function generateV2Keys(): { publicKey: V2PublicKey; secretKey: V2SecretKey } {
  const kem = ml_kem768.keygen();
  const xs = x25519.utils.randomSecretKey();
  return {
    publicKey: { kem: toB64(kem.publicKey), x: toB64(x25519.getPublicKey(xs)) },
    secretKey: { kem: toB64(kem.secretKey), x: toB64(xs) },
  };
}

async function fileKey(kemSecret: Uint8Array, dh: Uint8Array, salt: Uint8Array) {
  const ikm = new Uint8Array(kemSecret.length + dh.length);
  ikm.set(kemSecret, 0);
  ikm.set(dh, kemSecret.length);
  const raw = new Uint8Array(hkdf(sha256, ikm, salt, INFO, 32));
  return crypto.subtle.importKey("raw", raw, "AES-GCM", false, ["encrypt", "decrypt"]);
}

export async function sealV2(recipient: V2PublicKey, plaintext: Uint8Array<ArrayBuffer>): Promise<string> {
  const { cipherText, sharedSecret } = ml_kem768.encapsulate(fromB64(recipient.kem));
  const eph = x25519.utils.randomSecretKey();
  const epk = x25519.getPublicKey(eph);
  const dh = x25519.getSharedSecret(eph, fromB64(recipient.x));
  const key = await fileKey(sharedSecret, dh, epk);
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const data = new Uint8Array(await crypto.subtle.encrypt({ name: "AES-GCM", iv }, key, plaintext));
  const env: Envelope = { v: 2, ct: toB64(cipherText), epk: toB64(epk), iv: toB64(iv), data: toB64(data) };
  return btoa(JSON.stringify(env));
}

export async function openV2(secret: V2SecretKey, envelopeB64: string): Promise<Uint8Array> {
  const env = JSON.parse(atob(envelopeB64)) as Envelope;
  if (env.v !== 2) throw new Error("not a v2 share");
  const sharedSecret = ml_kem768.decapsulate(fromB64(env.ct), fromB64(secret.kem));
  const epk = fromB64(env.epk);
  const dh = x25519.getSharedSecret(fromB64(secret.x), epk);
  const key = await fileKey(sharedSecret, dh, epk);
  const out = await crypto.subtle.decrypt({ name: "AES-GCM", iv: fromB64(env.iv) }, key, fromB64(env.data));
  return new Uint8Array(out);
}
