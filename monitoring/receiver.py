import socket
import json
import os
import time
from datetime import datetime

from analyzer import (
    process_telemetry,
    start_analyzer,
    get_alerts,
    get_host_data
)

HOST = "0.0.0.0"
PORT = 9999

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "logs", "dashboard_data.json")

os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((HOST, PORT))

print("=" * 50)
print(" NETWORK MONITORING - UDP TELEMETRY RECEIVER")
print("=" * 50)
print(f"Listening on UDP port {PORT}...")
print("Waiting for host telemetry...\n")

start_analyzer()

received_packets = {}
alert_count = 0


def update_dashboard_data():
    data = {
        "status": "live",
        "updated_at": time.time(),
        "hosts": get_host_data(),
        "alerts": get_alerts(),
        "received_packets": received_packets.copy()
    }

    temp_file = DATA_FILE + ".tmp"

    with open(temp_file, "w") as file:
        json.dump(data, file)

    os.replace(temp_file, DATA_FILE)


while True:
    data, address = server.recvfrom(4096)

    try:
        telemetry = json.loads(data.decode())
        process_telemetry(telemetry)

        hostname = telemetry.get("host", "unknown")
        sequence = telemetry.get("sequence", 0)

        received_packets[hostname] = (
            received_packets.get(hostname, 0) + 1
        )

        timestamp = datetime.now().strftime("%H:%M:%S")

        print(
            f"[{timestamp}] "
            f"Host: {hostname} | "
            f"Sequence: {sequence} | "
            f"CPU: {telemetry.get('cpu_usage')}% | "
            f"Memory: {telemetry.get('memory_usage')}% | "
            f"Packets received: {received_packets[hostname]}"
        )

        current_alerts = get_alerts()

        if len(current_alerts) > alert_count:
            for alert in current_alerts[alert_count:]:
                print(f"\n🚨 ALERT: {alert}")

            alert_count = len(current_alerts)

        update_dashboard_data()

    except (json.JSONDecodeError, UnicodeDecodeError):
        print(f"Invalid telemetry packet from {address}")
    except OSError as error:
        print(f"Dashboard data write error: {error}")
