import { describe, expect, it } from "vitest";
import { generateV1KeyPair, openV1, sealV1 } from "./shareV1";
import { generateV2Keys, openV2, sealV2 } from "./shareV2";

const text = new TextEncoder().encode("quarterly report, final version");

describe("share v2", () => {
  it("round-trips", async () => {
    const { publicKey, secretKey } = generateV2Keys();
    const env = await sealV2(publicKey, text);
    expect(await openV2(secretKey, env)).toEqual(text);
  });

  it("rejects the wrong recipient", async () => {
    const alice = generateV2Keys();
    const bob = generateV2Keys();
    const env = await sealV2(alice.publicKey, text);
    await expect(openV2(bob.secretKey, env)).rejects.toThrow();
  });
});

describe("share v1", () => {
  it("still opens old shares", async () => {
    const pair = await generateV1KeyPair();
    const env = await sealV1(pair.publicJwk, text);
    expect(await openV1(pair.privateJwk, env)).toEqual(text);
  });
});
