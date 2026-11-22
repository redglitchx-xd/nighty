# apex-server in a container (docs/server.md, section 3). Build context: the repository root:
#   docker build -f packaging/server/Dockerfile -t apex-server .
#
# The image holds none of Minecraft's files. Prepare them on the host from your own Minecraft 26.3
# (apex-prepare --prepare, see packaging/PLAY.txt) and mount the folder it writes, read-only:
#   docker run -d --name apex -p 25565:25565 --stop-timeout 180 \
#     -v apex-data:/data \
#     -v /path/to/.local/apex-client/26.3:/opt/apex/.local/apex-client/26.3:ro \
#     -e APEX_EULA=true -e APEX_WHITELIST=true -e APEX_PLAYERS=Alex,Steve -e APEX_OP=Alex \
#     apex-server
#
# APEX_EULA=true accepts the Minecraft EULA (https://aka.ms/MinecraftEULA) for this server. The first
# start writes /data/server.toml from APEX_* (EULA, WORLD, SEED, PORT, WHITELIST, PLAYERS, OP); later
# starts use the file. Manage it with `docker exec apex apex-server status|cmd|backup|logs ...`.
FROM rust:1-slim-bookworm AS build
WORKDIR /src
COPY . .
# The server build of the game (no sound, no controllers: it needs neither ALSA nor udev) as apex-engine.
RUN cargo build --release --locked -p apex-client --no-default-features --bin apex-client \
    && cargo build --release --locked -p apex-server --bin apex-server \
    && mkdir /out && cp target/release/apex-client /out/apex-engine && cp target/release/apex-server /out/

FROM debian:bookworm-slim
RUN useradd --system --home-dir /data --shell /usr/sbin/nologin apex \
    && mkdir -p /data /opt/apex/.local/apex-client \
    && chown apex:apex /data
COPY --from=build /out/ /opt/apex/
ENV PATH=/opt/apex:$PATH \
    APEX_NO_AUDIO=1
WORKDIR /data
VOLUME /data
EXPOSE 25565
USER apex
# SIGTERM makes apex-server stop the game cleanly (it saves first): give it --stop-timeout 180.
CMD ["sh", "-c", "test -f server.toml || apex-server init --yes || exit 1; exec apex-server run"]
