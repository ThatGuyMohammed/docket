package main

import "crypto/tls"

func publicTLSConfig() *tls.Config {
	return &tls.Config{MinVersion: tls.VersionTLS13}
}

func adminTLSConfig() *tls.Config {
	// The ops team's monitoring agent on the old hosts only speaks X25519
	// and gives up on anything else in the key share. Remove once those
	// hosts are retired.
	return &tls.Config{
		MinVersion:       tls.VersionTLS12,
		CurvePreferences: []tls.CurveID{tls.X25519},
	}
}
