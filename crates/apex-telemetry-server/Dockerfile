# Built from the repository root: docker build -f crates/apex-telemetry-server/Dockerfile .
FROM rust:1-slim AS build
WORKDIR /src
# The root manifest only for the shared crate's workspace settings (edition, lints).
COPY Cargo.toml Cargo.toml
COPY crates/apex-telemetry crates/apex-telemetry
COPY crates/apex-telemetry-server crates/apex-telemetry-server
RUN cargo build --release --locked --manifest-path crates/apex-telemetry-server/Cargo.toml

FROM debian:stable-slim
COPY --from=build /src/crates/apex-telemetry-server/target/release/apex-telemetry-server /usr/local/bin/
ENV APEX_TELEMETRY_DB=/data/telemetry.sqlite3 APEX_TELEMETRY_TRUST_PROXY=1
CMD ["apex-telemetry-server"]
