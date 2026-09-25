package main

import (
	"crypto/ed25519"
	"crypto/rand"
	"encoding/base64"
	"testing"
)

func TestVerifyPartner(t *testing.T) {
	pub, priv, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		t.Fatal(err)
	}
	var key [32]byte
	copy(key[:], pub)
	body := []byte(`{"type":"document.countersigned"}`)
	sig := base64.StdEncoding.EncodeToString(ed25519.Sign(priv, body))

	if err := verifyPartner(key, body, sig); err != nil {
		t.Fatalf("valid signature rejected: %v", err)
	}
	if err := verifyPartner(key, append(body, ' '), sig); err == nil {
		t.Fatal("tampered body accepted")
	}
	if err := verifyPartner(key, body, "AAAA"); err == nil {
		t.Fatal("short signature accepted")
	}
}
