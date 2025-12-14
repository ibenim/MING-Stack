# IoT Monitoring Stack: Node-RED → MQTT → Telegraf → InfluxDB → Grafana

A lightweight, self-contained IoT monitoring playground implemented with Docker Compose. It runs 10 virtual Node‑RED sensors that publish JSON payloads to an MQTT broker (Mosquitto); Telegraf subscribes and writes time-series data to InfluxDB; Grafana auto-provisions dashboards for quick visualization. Designed for local development on Windows/macOS/Linux, with host-mounted persistence and guidance for Docker Desktop quirks.

```
Node-RED (10 virtual sensors)
      ↓ MQTT
   Mosquitto (broker)
      ↓
   Telegraf (subscriber)
      ↓
   InfluxDB 2.x (time-series database)
      ↓
   Grafana (beautiful dashboards)
```

Architecture
```
Node-RED (10 virtual sensors)

Features
- 10 realistic virtual sensors with different sampling rates (4 s – 2 min)
- Clean JSON payloads: `{"value": 23.7}`
- Persistent storage:

Quick Start (5 minutes)

```bash
# 1. Clone or create project folder

# 2. Create directories (Windows PowerShell example)
mkdir -p mosquitto/config mosquitto/data mosquitto/log node-red telegraf influxdb/data grafana/provisioning/datasources grafana/provisioning/dashboards grafana/dashboard

# 3. Copy repository files into this folder or clone the repo
```

Compose and config (example files are included in this repo)

The repository contains a `docker-compose.yml` that starts Mosquitto, Node-RED, InfluxDB, Telegraf and Grafana. Key points:

- InfluxDB persistence is mounted to `./influxdb/data`
- Telegraf reads `INFLUX_TOKEN` from environment (set in `docker-compose.yml` or `.env`)
- Grafana auto-imports dashboards from `./grafana/dashboard` via provisioning

Example Telegraf snippet (from `telegraf/telegraf/telegraf.conf`):

```toml
[[outputs.influxdb_v2]]

Grafana provisioning (examples live under `grafana/provisioning` in the repo). Dashboards placed in `grafana/dashboard` will be copied into Grafana's provisioning folder at container start so they are auto-imported.

Start the stack

```powershell
# On Windows (PowerShell)
docker compose up -d

Access the tools

| Service     | URL                          | Login                  | Notes                              |
|-------------|------------------------------|------------------------|------------------------------------|
| Grafana     | http://localhost:3000        | admin / grafana123     | Dashboards auto-loaded             |
| Node-RED    | http://localhost:1880        | (no login)             | 10 sensors already running         |
| InfluxDB    | http://localhost:8086        | admin / admin123       | Bucket: `sensors` (if first-time)  |

Developer notes

Node-RED flows
- `node-red/flows.json` is provided as the initial flows file. On Windows the compose file mounts it read-only into the container and the container copies it into `/data/flows.json` at startup. This avoids Docker Desktop file-vs-dir bind problems and EBUSY/rename errors while still starting Node-RED with reproducible flows.

- To persist runtime edits back to the host, change the `node-red` service volumes in `docker-compose.yml` to bind `./node-red/flows.json:/data/flows.json` and remove the startup copy command — be aware this may reintroduce Windows mount issues.

Telegraf and tokens
- `telegraf/telegraf/telegraf.conf` is mounted from the repo directory. To avoid Windows mount/file confusion, the whole `telegraf/telegraf` directory is mounted.

- Telegraf reads `INFLUX_TOKEN` from the environment. You can set it in `docker-compose.yml` or in a `.env` file at the repo root:

```
INFLUX_TOKEN=yourtokenhere
```

InfluxDB data persistence
- All InfluxDB data is saved in `./influxdb/data` on your host.
- If InfluxDB finds an existing BoltDB file in that directory, the initial setup (the `DOCKER_INFLUXDB_INIT_*` env vars) will be skipped and logs show: `found existing boltdb file, skipping setup wrapper`.
  - If you expect a fresh install but see that log, either back up and remove `./influxdb/data` or keep the data and create tokens/users manually in the InfluxDB UI.

Grafana dashboards
- The repo contains dashboard files in `grafana/dashboard` (JSON/YAML). The compose setup copies any `*.json` files into Grafana's provisioning dashboards directory at container start so dashboards like `sensorsv2.json` are auto-imported.
- If you have a YAML dashboard (e.g. `sensorsv2.yaml`), convert it to JSON before start using `yq` or Python (examples below).

Telegraf config synchronization
If you register a Telegraf configuration inside InfluxDB (remote Telegraf configs) and also use a local Telegraf config file, keep them in sync:

View local repo copy:
```bash
cat telegraf/telegraf/telegraf.conf
```

View container copy:
```bash
docker compose exec telegraf cat /etc/telegraf/telegraf.conf
```

Register the same config in InfluxDB via API (example):
```bash
export INFLUX_TOKEN="your-token"
export INFLUX_URL="http://localhost:8086"
curl -sS -X POST "$INFLUX_URL/api/v2/telegrafs?org=home" \
  -H "Authorization: Token $INFLUX_TOKEN" \
  -H "Content-Type: application/json" \
  --data-binary @- <<'JSON'
{
  "name": "telegraf-from-repo",
  "active": true,
  "config": "$(sed -e 's/\\/\\\\/g' -e ':a;N;$!ba;s/\n/\\n/g' telegraf/telegraf/telegraf.conf)"
}
JSON
```

Notes:
- The `config` value must be a JSON string; the example above escapes newlines. Use a small helper script for robust handling.
- Confirm registered configs with:
```
curl -H "Authorization: Token $INFLUX_TOKEN" $INFLUX_URL/api/v2/telegraf
```

Grafana YAML→JSON conversion examples

Bash (requires `yq`):
```bash
yq -o=json . grafana/dashboard/sensorsv2.yaml > grafana/dashboard/sensorsv2.json
```

PowerShell (using Python):
```powershell
python -c "import sys,yaml,json; print(json.dumps(yaml.safe_load(sys.stdin)))" < grafana/dashboard/sensorsv2.yaml > grafana/dashboard/sensorsv2.json
```

Useful commands
```bash
docker compose up -d              # Start all services
docker compose down               # Stop (data stays)
docker compose down -v            # Full wipe (deletes data!)
docker compose restart node-red   # Reload flows after editing flows.json
docker compose logs -f mosquitto  # Watch MQTT traffic
docker compose logs -f telegraf   # Watch data ingestion
```

PowerShell checks
```powershell
docker info
docker compose up -d
docker compose logs -f influxdb
```

Windows Docker Desktop notes
- Docker Desktop must be running before `docker compose up`. If you see errors like `open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified`, start Docker Desktop and retry.
- On Windows prefer directory mounts and copy-on-start patterns for files Node-RED or other apps write to, to avoid bind/lock errors.

Git and repo tips
- Avoid committing large DB files and logs. Add a `.gitignore` with entries such as:
```
influxdb/data/
mosquitto/log/
mosquitto/data/
.env
*.log
```



Enjoy your IoT playground — great for learning, testing, and demos. 🚀
# IoT Stack (Node-RED, Mosquitto, InfluxDB, Telegraf, Grafana)


Key notes for developers

- Node-RED flows are provided in `node-red/flows.json` and are mounted into the
  container at startup as a read-only file. The compose setup copies that file
  into the container's runtime `/data` directory on start so Node-RED **starts
  with the supplied flows but any runtime edits are not persisted back to the
  host**.

  Why we do this:
  - Mounting a host file directly into Node-RED's writable `/data` on Windows
    can cause file-vs-directory bind problems and EBUSY/rename errors when the
    app creates temporary files (see earlier `flows.json.$$$` errors).
  - To avoid those runtime mount and lock issues while keeping a reproducible
    startup state, the repo provides `flows.json` as a read-only initial file
    which is copied into the container at start.

  How to persist Node-RED edits (if you want persistent flows):
  - Edit `docker-compose.yml` and change the `node-red` service volumes:
    uncomment or add a bind mount like `- ./node-red/flows.json:/data/flows.json`
    and remove the startup `cp` command so the container writes directly to
    the host file. Be aware this may reintroduce Windows mount/lock issues.

- MQTT / Network configuration
  - All services are placed on the `iot-net` Docker network so they can
    resolve each other by service name.
  - Node-RED and Telegraf must use the Compose service name `mosquitto` (not
    a container IP) as the MQTT broker host, e.g. `broker: "mosquitto"` in
    `node-red/flows.json` and `servers = ["tcp://mosquitto:1883"]` in
    `telegraf/telegraf/telegraf.conf`.
  - Do not hardcode container IPs; service names are stable across restarts.

Other Telegraf / Influx tips
 - `telegraf/telegraf/telegraf.conf` is mounted from the repo directory
   (the whole `telegraf/telegraf` directory is mounted to avoid Windows
   file-vs-directory bind issues).
 - Telegraf reads `INFLUX_TOKEN` from the environment (set in
   `docker-compose.yml`) and is started with the local config file to avoid
   remote-config HTTP attempts.
 - The config subscribes to `home/#` (sensor topics). Avoid `json_query` that
   selects a primitive (number/string) — Telegraf expects the query path to
   result in an object/array/null.

Start the stack

```powershell
docker-compose up -d
docker-compose logs -f mosquitto telegraf node-red influxdb grafana
```

If anything here is unclear or you want me to change the compose behavior (e.g.
make Node-RED edits persistent or persist telegraf config another way), tell
me which option you prefer and I will prepare the changes.

## Telegraf config synchronization

If you use a local Telegraf config (the repository file `telegraf/telegraf/telegraf.conf`) and also register a Telegraf configuration inside InfluxDB (remote Telegraf configs), keep them identical so ingestion behaves predictably.

- View the local repo copy:

```bash
cat telegraf/telegraf/telegraf.conf
```

- View the file used by the running container:

```bash
docker compose exec telegraf cat /etc/telegraf/telegraf.conf
```

- Quick checksum comparison (Linux / Git Bash):

```bash
sha256sum telegraf/telegraf/telegraf.conf /dev/fd/0 <<<'$(docker compose exec telegraf cat /etc/telegraf/telegraf.conf)'
```

- Register the same config in InfluxDB via API (example):

```bash
export INFLUX_TOKEN="your-token"
export INFLUX_URL="http://localhost:8086"
curl -sS -X POST "$INFLUX_URL/api/v2/telegrafs?org=home" \
  -H "Authorization: Token $INFLUX_TOKEN" \
  -H "Content-Type: application/json" \
  --data-binary @- <<'JSON'
{
  "name": "telegraf-from-repo",
  "active": true,
  "config": "$(sed -e 's/\\/\\\\/g' -e ':a;N;$!ba;s/\n/\\n/g' telegraf/telegraf/telegraf.conf)"
}
JSON
```

Notes:
- The `config` value must be a JSON string; the example above escapes newlines. Use a small script for more robust handling.
- Confirm registered configs with: `curl -H "Authorization: Token $INFLUX_TOKEN" $INFLUX_URL/api/v2/telegrafs`
