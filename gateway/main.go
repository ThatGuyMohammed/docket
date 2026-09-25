package main

import (
	"context"
	"errors"
	"log"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"
	"os/signal"
	"sync/atomic"
	"syscall"
	"time"
)

var requests atomic.Int64

func countRequests(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		requests.Add(1)
		next.ServeHTTP(w, r)
	})
}

func newRouter(cfg *Config, upstream *url.URL) http.Handler {
	proxy := httputil.NewSingleHostReverseProxy(upstream)
	mux := http.NewServeMux()
	mux.Handle("POST /api/webhooks/inbound", partnerMiddleware(cfg, proxy))
	mux.Handle("/", proxy)
	return countRequests(mux)
}

func adminRouter() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /healthz", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("ok\n"))
	})
	mux.HandleFunc("GET /metrics", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/plain; version=0.0.4")
		w.Write([]byte("docket_gateway_requests_total " + itoa(requests.Load()) + "\n"))
	})
	return mux
}

func itoa(n int64) string {
	if n == 0 {
		return "0"
	}
	var b [20]byte
	i := len(b)
	for n > 0 {
		i--
		b[i] = byte('0' + n%10)
		n /= 10
	}
	return string(b[i:])
}

func main() {
	cfg, err := loadConfig()
	if err != nil {
		log.Fatal(err)
	}
	upstream, err := url.Parse(cfg.Upstream)
	if err != nil {
		log.Fatalf("UPSTREAM_URL: %v", err)
	}

	public := &http.Server{
		Addr:              cfg.Listen,
		Handler:           newRouter(cfg, upstream),
		TLSConfig:         publicTLSConfig(),
		ReadHeaderTimeout: 10 * time.Second,
	}
	admin := &http.Server{
		Addr:              cfg.AdminListen,
		Handler:           adminRouter(),
		TLSConfig:         adminTLSConfig(),
		ReadHeaderTimeout: 10 * time.Second,
	}

	for _, srv := range []*http.Server{public, admin} {
		go func(s *http.Server) {
			log.Printf("listening on %s", s.Addr)
			if err := s.ListenAndServeTLS(cfg.CertFile, cfg.KeyFile); !errors.Is(err, http.ErrServerClosed) {
				log.Fatal(err)
			}
		}(srv)
	}

	stop := make(chan os.Signal, 1)
	signal.Notify(stop, syscall.SIGINT, syscall.SIGTERM)
	<-stop
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	public.Shutdown(ctx)
	admin.Shutdown(ctx)
}
