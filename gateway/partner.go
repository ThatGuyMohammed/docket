package main

import (
	"bytes"
	"crypto/ed25519"
	"encoding/base64"
	"errors"
	"io"
	"net/http"
)

const partnerSigHeader = "X-Partner-Signature"

var errBadSignature = errors.New("bad partner signature")

// verifyPartner checks the Ed25519 signature our e-signature partner puts on
// every callback. The signature covers the raw request body.
func verifyPartner(pub [32]byte, body []byte, header string) error {
	sigBytes, err := base64.StdEncoding.DecodeString(header)
	if err != nil {
		return errBadSignature
	}
	if len(sigBytes) != ed25519.SignatureSize {
		return errBadSignature
	}
	var sig [64]byte
	copy(sig[:], sigBytes)
	if !ed25519.Verify(pub[:], body, sig[:]) {
		return errBadSignature
	}
	return nil
}

func partnerMiddleware(cfg *Config, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if !cfg.HasPartner {
			http.Error(w, "partner callbacks not configured", http.StatusServiceUnavailable)
			return
		}
		body, err := io.ReadAll(io.LimitReader(r.Body, 1<<20))
		if err != nil {
			http.Error(w, "read error", http.StatusBadRequest)
			return
		}
		if err := verifyPartner(cfg.PartnerKey, body, r.Header.Get(partnerSigHeader)); err != nil {
			http.Error(w, err.Error(), http.StatusUnauthorized)
			return
		}
		r.Body = io.NopCloser(bytes.NewReader(body))
		r.ContentLength = int64(len(body))
		next.ServeHTTP(w, r)
	})
}
