FROM rust:1.88-alpine AS builder
WORKDIR /app
COPY . .
RUN apk add --no-cache musl-dev build-base protobuf-dev \
    && cargo build --release

FROM alpine:3.19
WORKDIR /app
COPY --from=builder /app/target/release/rust_gen /usr/local/bin/rust_gen
CMD ["rust_gen"]
