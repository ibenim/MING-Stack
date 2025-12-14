# IoT Monitoring Stack: MQTT → InfluxDB → Grafana
**10 Virtual Sensors with Docker Compose**
*December 2025 – Fully working, persistent, beginner-friendly*

This stack runs a complete IoT monitoring pipeline on your laptop or VPS:

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

All services communicate over a bridged Docker network.
Data from all sensors is stored **on your laptop** (host) in a local folder when you use the provided compose mounts.

## Features
- 10 realistic virtual sensors with different sampling rates (4 s – 2 min)
- Clean JSON payloads: `{"value": 23.7}`
- Persistent storage:
  - InfluxDB data → `./influxdb/data` (survives restarts & `docker compose down`)
  - Node-RED flows → provided via `node-red/flows.json`. On Windows the flows file is mounted read-only and copied into the container at startup to avoid Docker Desktop file-lock issues.
  - Grafana settings → persistent volume
- Auto-provisioned Grafana datasource
- Ready for real sensors (just publish to `home/#` topics)
- Easy to extend with real MQTT devices later

## Quick Start (5 minutes)

```bash
# 1. Create project folder
mkdir ~/iot-stack && cd ~/iot-stack

# 2. Create all folders
mkdir -p mosquitto/{config,data,log} node-red telegraf influxdb/data grafana/provisioning/{datasources,dashboards} grafana/dashboards

# 3. Download docker-compose.yml and configs (copy-paste the full block below)
```

**Paste this entire block into your terminal** (it creates all files automatically):

```bash
cat > docker-compose.yml <<'EOF'
version: "3.9"

services:
  mosquitto:
    image: eclipse-mosquitto:latest
    container_name: mosquitto
    restart: unless-stopped
    ports:
      - "1883:1883"
      - "9001:9001"
    volumes:
      - ./mosquitto/config:/mosquitto/config
      - ./mosquitto/data:/mosquitto/data
      - ./mosquitto/log:/mosquitto/log
    networks:
      - iot-net

  node-red:
    image: nodered/node-red:latest
    container_name: node-red
    restart: unless-stopped
    ports:
      - "1880:1880"
    volumes:
      - node-red-data:/data
      - ./node-red/flows.json:/data/flows.json:ro
    depends_on:
      - mosquitto
    networks:
      - iot-net

  influxdb:
    image: influxdb:2.7
    container_name: influxdb
    restart: unless-stopped
    ports:
      - "8086:8086"
    environment:
      - DOCKER_INFLUXDB_INIT_MODE=setup
      - DOCKER_INFLUXDB_INIT_USERNAME=admin
      - DOCKER_INFLUXDB_INIT_PASSWORD=admin123
      - DOCKER_INFLUXDB_INIT_ORG=home
      - DOCKER_INFLUXDB_INIT_BUCKET=sensors
      - DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=mysecretlongtoken1234567890
    volumes:
      - ./influxdb/data:/var/lib/influxdb2   # Persistent on your laptop!
    networks:
      - iot-net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8086/ping"]
      interval: 10s
      retries: 10

  telegraf:
    image: telegraf:1.30-alpine
    container_name: telegraf
    restart: unless-stopped
    depends_on:
      influxdb:
        condition: service_healthy
      mosquitto:
        condition: service_started
    volumes:
      - ./telegraf/telegraf.conf:/etc/telegraf/telegraf.conf:ro
    environment:
      - INFLUX_TOKEN=mysecretlongtoken1234567890
    networks:
      - iot-net

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=grafana123
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
    depends_on:
      - influxdb
    networks:
      - iot-net

networks:
  iot-net:
    driver: bridge

volumes:
  node-red-data:
  grafana-data:
EOF

# Mosquitto config
cat > mosquitto/config/mosquitto.conf <<'EOF'
persistence true
persistence_location /mosquitto/data/
log_dest file /mosquitto/log/mosquitto.log
log_dest stdout
listener 1883
allow_anonymous true
listener 9001
protocol websockets
allow_anonymous true
EOF

# Telegraf config
cat > telegraf/telegraf.conf <<'EOF'
[[outputs.influxdb_v2]]
  urls = ["http://influxdb:8086"]
  # Telegraf reads the token from the environment variable `INFLUX_TOKEN` (set in docker-compose.yml)
  token = "${INFLUX_TOKEN}"
  organization = "home"
  bucket = "sensors"

[[inputs.mqtt_consumer]]
  servers = ["tcp://mosquitto:1883"]
  topics = ["home/#"]
  data_format = "json"
EOF

# Grafana datasource provisioning
cat > grafana/provisioning/datasources/influxdb.yml <<'EOF'
apiVersion: 1
datasources:
  - name: InfluxDB
    type: influxdb
    access: proxy
    url: http://influxdb:8086
    jsonData:
      version: Flux
      organization: home
      defaultBucket: sensors
      token: mysecretlongtoken1234567890
    secureJsonData:
      token: mysecretlongtoken1234567890
    isDefault: true
EOF

# Grafana dashboard provisioning
cat > grafana/provisioning/dashboards/provision.yaml <<'EOF'
apiVersion: 1
providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
EOF

# 10-sensor Node-RED flows (100% working)
curl -fsSL https://raw.githubusercontent.com/chrisb89/mqtt-influx-grafana-stack/main/node-red/flows.json > node-red/flows.json
```

```bash
# 4. Start everything
docker compose up -d

# Wait ~60 seconds for first-time InfluxDB setup
```

## Access the Tools

| Service     | URL                          | Login                  | Notes                              |
|-------------|------------------------------|------------------------|------------------------------------|
| Grafana     | http://localhost:3000        | admin / grafana123     | Dashboards auto-loaded             |
| Node-RED    | http://localhost:1880        | (no login)             | 10 sensors already running         |
| InfluxDB    | http://localhost:8086        | admin / admin123       | Bucket: `sensors`                  |
| MQTT Broker | localhost:1883 (plain)       | anonymous              | WebSocket: localhost:9001          |

## The 10 Virtual Sensors

| Sensor                | Topic                              | Interval | Range               |
|-----------------------|------------------------------------|----------|---------------------|
| Living Room Temp      | home/livingroom/temperature        | 8 s      | 20–28 °C            |
| Kitchen Humidity      | home/kitchen/humidity              | 15 s     | 40–65 %             |
| Outdoor Temp          | home/outdoor/temperature           | 30 s     | 5–35 °C             |
| Bedroom CO₂           | home/bedroom/co2                   | 45 s     | 400–1600 ppm        |
| Office Light          | home/office/light                  | 4 s      | 100–1000 lux        |
| Basement Pressure     | home/basement/pressure             | 60 s     | 980–1030 hPa        |
| Garage Soil Moisture  | home/garage/soil_moisture          | 2 min    | 20–80 %             |
| Attic VOC             | home/attic/voc                     | 20 s     | 50–1000 ppb         |
| Balcony Wind Speed    | home/balcony/wind_speed            | 10 s     | 0–25 km/h           |
| Server Room Noise     | home/serverroom/noise_db           | 6 s      | 30–70 dB            |

## Data Persistence
- All InfluxDB data is saved in **`./influxdb/data`** on your laptop (host path mounted into the container)
- If InfluxDB finds an existing internal BoltDB file in that directory, the built-in one-time setup (the `DOCKER_INFLUXDB_INIT_*` env vars) will be skipped — you will see a log like: `found existing boltdb file, skipping setup wrapper`.
  - If you expect a fresh install but see that log, either back up and remove the host `./influxdb/data` directory (wiping existing data) or keep the data and manually create tokens/users inside the running InfluxDB UI.
- Survives `docker compose down`, container deletion, or reboots
- Easy backup (PowerShell example):

```powershell
Copy-Item -Recurse .\influxdb\data C:\backups\iot-influxdb-$(Get-Date -Format yyyy-MM-dd)
```

## Useful Commands

Docker on Windows (Docker Desktop) must be running before you `docker compose up` — if you see errors like "open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified", start Docker Desktop and retry.

Linux/macOS / WSL / PowerShell examples:

```bash
docker compose up -d              # Start
docker compose down               # Stop (data stays)
docker compose down -v            # Full wipe (deletes data!)
docker compose restart node-red   # Reload flows after editing flows.json (container copies flows.json into /data at startup)
docker compose logs -f mosquitto  # Watch MQTT traffic
docker compose logs -f telegraf   # Watch data ingestion
```

PowerShell (Windows) to check Docker and start the stack:

```powershell
docker info                      # verifies Docker daemon is accessible
docker compose up -d
docker compose logs -f influxdb
```

If InfluxDB reports it found an existing BoltDB file and skipped initial setup, you can:

- Keep the data: sign in to InfluxDB UI and create tokens/users manually
- Back up & reset: stop containers, move `./influxdb/data` to a backup path, then `docker compose up -d` for a fresh init

On Windows there are known file-mount/locking edge-cases. This repo uses directory mounts and a copy-at-start approach for `node-red/flows.json` to avoid file-locking issues on Docker Desktop.

## Grafana Dashboards
- Dashboards placed in the repository `grafana/dashboard` are auto-imported on container start. The compose setup copies any `*.json` files from `./grafana/dashboard` into Grafana's provisioning folder so they appear automatically (this includes `sensorsv2.json`).
- If you prefer YAML dashboards (e.g. `sensorsv2.yaml`) you can either commit the JSON export (`sensorsv2.json`) or convert YAML to JSON before starting Grafana. Example converters:

  Bash (requires `yq`):

  ```bash
  yq -o=json . grafana/dashboard/sensorsv2.yaml > grafana/dashboard/sensorsv2.json
  ```

  PowerShell (using Python if installed):

  ```powershell
  python -c "import sys,yaml,json; print(json.dumps(yaml.safe_load(sys.stdin)))" < grafana/dashboard/sensorsv2.yaml > grafana/dashboard/sensorsv2.json
  ```

- Troubleshooting: if dashboards do not appear after Grafana starts, check the Grafana container logs for provisioning errors:

```bash
docker compose logs -f grafana
```

Look for messages about provisioning or invalid dashboard files and fix any JSON/YAML syntax issues before retrying.

## Next Steps
- Add a real ESP32/ESP8266 sensor → publish to any `home/#` topic
- Create custom Grafana dashboards
- Add HTTPS reverse proxy (Caddy/Traefik)
- Enable MQTT authentication

Enjoy your instant IoT playground — perfect for learning, testing, or building real projects! 🚀