# IoT Stack (Node-RED, Mosquitto, InfluxDB, Telegraf, Grafana)

This repository runs a small IoT simulation stack using Docker Compose.

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
