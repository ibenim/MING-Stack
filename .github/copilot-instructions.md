# Copilot instructions for this repository

Purpose
- Help AI coding agents become productive quickly with this IoT-compose stack.

Big picture (what runs and why)
- MQTT broker: `mosquitto` provides topics for sensors (ports 1883 and websocket 9001).
- Node-RED: `node-red` generates/publishes simulated sensor messages to MQTT (flows in `node-red/flows.json`).
- Time-series DB: `influxdb` stores sensor data (initialized via `DOCKER_INFLUXDB_INIT_*` envs in `docker-compose.yml`).
- Telegraf: `telegraf` subscribes to MQTT and writes to InfluxDB using `telegraf/telegraf.conf`.

Key integration patterns (exact, copyable)
- MQTT topic convention: `home/<room>/<metric>` (see many `inject` nodes in `node-red/flows.json`).
- Node-RED payload shape: JSON with a `value` field. Example function node sets `msg.payload = { value: 23.5 }`.
- Telegraf expects JSON `value` field: `data_format = "json"` and `json_query = "value"` in `telegraf/telegraf.conf`.
- Influx tokens: `DOCKER_INFLUXDB_INIT_ADMIN_TOKEN` (compose) must match `INFLUX_TOKEN` used by Telegraf.

Where to look (most-important files)
- `docker-compose.yml` — service definitions, ports, volumes, envs, healthchecks.
- `mosquitto/config/mosquitto.conf` — listeners, persistence path, websockets port 9001.
- `node-red/flows.json` — Node-RED flows and MQTT publish wiring (inject → function → mqtt out).
- `telegraf/telegraf/telegraf.conf` — MQTT consumer input and InfluxDB v2 output.

Developer workflows (commands and expectations)
- Start stack (background):

```powershell
docker-compose up -d
```

- See container logs (example):

```powershell
docker-compose logs -f mosquitto
docker-compose logs -f telegraf
```

- InfluxDB health check: `curl http://localhost:8086/ping` (compose already uses this for healthchecks).

Conventions and gotchas (project-specific)
- Node-RED flows are present in `node-red/flows.json`, but the bind mount is commented out in `docker-compose.yml`. To persist or edit flows from the host, uncomment the `volumes:` lines under `node-red`.
- MQTT messages must be JSON objects with a `value` key; Telegraf uses `json_query = "value"` to extract it.
- Mosquitto permits anonymous access in current config (`allow_anonymous true`) — authentication is not configured by default.

Small examples (how to add a new sensor)
- Add a Node-RED inject node that publishes to topic `home/attic/temperature` and set payload via function to `msg.payload = { value: 21.2 }`.
- Confirm Telegraf sees it by checking `telegraf` logs; confirm Influx by querying the `sensors` bucket in InfluxDB UI or via API.

Troubleshooting hints
- MQTT broker logs: `./mosquitto/log/mosquitto.log`.
- If Telegraf fails to write: confirm `INFLUX_TOKEN` matches the InfluxDB admin token and that `influxdb` is healthy.
- If Node-RED flows don't appear to change, check whether `node-red` is using container-local storage (flows mount commented).

When to ask the user
- If you need secrets (Influx tokens) or want persistent Node-RED flows enabled, ask whether to enable bind mounts and where to store secrets.

If anything here is unclear or you want more examples (e.g., how to add an authenticated Mosquitto user or persist Node-RED flows), tell me which part to expand.
