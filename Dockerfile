FROM caddy:2-builder AS builder

RUN xcaddy build \
    --with github.com/mholt/caddy-ratelimit

FROM cgr.dev/chainguard/static:latest

LABEL org.opencontainers.image.authors="m@tusk.sh"
LABEL com.tusk.version="0.3"
LABEL com.tusk.release-date="07.11.2025"
LABEL cgr.dev.release-date="2025-11-07"


COPY --from=builder /usr/bin/caddy /usr/bin/caddy

ENTRYPOINT ["/usr/bin/caddy"]
CMD ["run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"]