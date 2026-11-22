# The Play with friends relay, for anyone to run (docs/play-with-friends.md, "Running your own relay").
# Build context: the repository root (the workspace's manifests and lockfile):
#   docker build -f crates/apex-relay/Dockerfile -t apex-relay .
FROM rust:1-slim-bookworm AS build
WORKDIR /src
COPY . .
RUN cargo build --release --locked -p apex-relay \
    && cp target/release/apex-relay /apex-relay

FROM debian:bookworm-slim
COPY --from=build /apex-relay /usr/local/bin/apex-relay
ENV PORT=7000
EXPOSE 7000
USER nobody
CMD ["apex-relay"]
