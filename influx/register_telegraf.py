#!/usr/bin/env python3
import json
import os
import time
import urllib.request

TOKEN = os.environ.get('DOCKER_INFLUXDB_INIT_ADMIN_TOKEN') or os.environ.get('INFLUX_TOKEN')
ORG = os.environ.get('DOCKER_INFLUXDB_INIT_ORG', 'home')
URL = f'http://influxdb:8086/api/v2/telegrafs?org={ORG}'
CONF_PATH = '/etc/telegraf/telegraf.conf'

def main():
    if not TOKEN:
        print('ERROR: No token found in env DOCKER_INFLUXDB_INIT_ADMIN_TOKEN or INFLUX_TOKEN')
        return 2
    # wait for influx to be ready
    for i in range(30):
        try:
            req = urllib.request.Request('http://influxdb:8086/health')
            with urllib.request.urlopen(req, timeout=5) as r:
                if r.status == 200:
                    break
        except Exception:
            time.sleep(1)
    else:
        print('InfluxDB not healthy, aborting')
        return 3

    try:
        with open(CONF_PATH, 'r', encoding='utf-8') as f:
            conf = f.read()
    except Exception as e:
        print('Failed to read telegraf conf:', e)
        return 4

    payload = {
        'name': 'telegraf-from-compose',
        'description': 'Telegraf config imported from compose',
        'telegraf': conf,
        'active': True
    }
    data = json.dumps(payload).encode('utf-8')
    headers = {
        'Authorization': 'Token ' + TOKEN,
        'Content-Type': 'application/json'
    }

    req = urllib.request.Request(URL, data=data, headers=headers, method='POST')
    for attempt in range(10):
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                print('Influx telegraf create response:', resp.status)
                body = resp.read().decode('utf-8')
                print(body)
                return 0
        except Exception as e:
            print('POST attempt', attempt, 'failed:', e)
            time.sleep(2)
    print('Failed to POST telegraf config after retries')
    return 5

if __name__ == '__main__':
    raise SystemExit(main())
