import csv
import json
import os
import time
from datetime import datetime

DATA_FILE = "logs/dashboard_data.json"
OUTPUT_FILE = "results/performance_metrics.csv"

os.makedirs("results", exist_ok=True)

previous = {}
fields = [
    "timestamp", "host", "online", "cpu_percent",
    "memory_percent", "sequence", "packets_received",
    "packet_rate_pps", "estimated_missing_packets"
]

with open(OUTPUT_FILE, "w", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=fields)
    writer.writeheader()

    print("=" * 55)
    print(" NETWORK MONITORING - PERFORMANCE EVALUATION")
    print("=" * 55)
    print("Sampling every second. Collect for at least 60 seconds.")
    print("Press Ctrl+C to stop and save results.\n")

    try:
        while True:
            try:
                with open(DATA_FILE) as source:
                    data = json.load(source)

                now = time.time()
                hosts = data.get("hosts", {})
                counts = data.get("received_packets", {})
                online_count = 0

                for host, info in hosts.items():
                    sequence = int(info.get("sequence", 0))
                    received = int(counts.get(host, 0))
                    online = now - float(info.get("last_seen", 0)) <= 15
                    online_count += int(online)

                    old = previous.get(host)

                    if old:
                        elapsed = max(now - old["time"], 0.001)
                        packet_delta = max(received - old["received"], 0)
                        rate = packet_delta / elapsed
                        missing = max(
                            (sequence - old["sequence"]) - packet_delta, 0
                        ) if sequence >= old["sequence"] else 0
                    else:
                        rate = 0
                        missing = 0

                    writer.writerow({
                        "timestamp": datetime.now().isoformat(timespec="seconds"),
                        "host": host,
                        "online": online,
                        "cpu_percent": info.get("cpu", 0),
                        "memory_percent": info.get("memory", 0),
                        "sequence": sequence,
                        "packets_received": received,
                        "packet_rate_pps": round(rate, 3),
                        "estimated_missing_packets": missing
                    })

                    previous[host] = {
                        "time": now,
                        "sequence": sequence,
                        "received": received
                    }

                file.flush()
                print(f"[{datetime.now():%H:%M:%S}] Online: {online_count}/6")

            except (FileNotFoundError, json.JSONDecodeError):
                print("Waiting for receiver data...")

            time.sleep(1)

    except KeyboardInterrupt:
        print("\nEvaluation stopped. Results saved:", OUTPUT_FILE)
