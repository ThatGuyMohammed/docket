package main

import (
	"encoding/base64"
	"fmt"
	"os"
)

type Config struct {
	Listen      string
	AdminListen string
	CertFile    string
	KeyFile     string
	Upstream    string
	PartnerKey  [32]byte
	HasPartner  bool
}

func env(name, def string) string {
	if v := os.Getenv(name); v != "" {
		return v
	}
	return def
}

func loadConfig() (*Config, error) {
	cfg := &Config{
		Listen:      env("GATEWAY_LISTEN", ":8443"),
		AdminListen: env("GATEWAY_ADMIN_LISTEN", ":9443"),
		CertFile:    env("TLS_CERT_FILE", "/certs/tls.crt"),
		KeyFile:     env("TLS_KEY_FILE", "/certs/tls.key"),
		Upstream:    env("UPSTREAM_URL", "http://api:8000"),
	}
	if raw := os.Getenv("PARTNER_PUBLIC_KEY"); raw != "" {
		b, err := base64.StdEncoding.DecodeString(raw)
		if err != nil {
			return nil, fmt.Errorf("PARTNER_PUBLIC_KEY: %w", err)
		}
		if len(b) != len(cfg.PartnerKey) {
			return nil, fmt.Errorf("PARTNER_PUBLIC_KEY: want %d bytes, got %d", len(cfg.PartnerKey), len(b))
		}
		copy(cfg.PartnerKey[:], b)
		cfg.HasPartner = true
	}
	return cfg, nil
}
