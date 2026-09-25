FROM golang:1.24 AS build
WORKDIR /src
COPY gateway/go.mod ./
COPY gateway/*.go ./
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/gateway .

FROM gcr.io/distroless/static-debian12
COPY --from=build /out/gateway /gateway
EXPOSE 8443 9443
ENTRYPOINT ["/gateway"]
