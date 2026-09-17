FROM rust:1.88-alpine AS builder
WORKDIR /app
COPY . .
# musl-dev + build-base are needed to compile ring (used by rustls).
# protobuf-dev is needed for tonic/gRPC.
RUN apk add --no-cache musl-dev build-base protobuf-dev \
    && cargo build --release

FROM alpine:3.19
WORKDIR /app
# ca-certificates lets rustls validate TLS certs for any external calls.
RUN apk add --no-cache ca-certificates
COPY --from=builder /app/target/release/checkout /usr/local/bin/checkout
CMD ["checkout"]
