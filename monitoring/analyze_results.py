import csv
import os
from datetime import datetime
from collections import defaultdict
import matplotlib.pyplot as plt

source = "results/performance_metrics.csv"
os.makedirs("results", exist_ok=True)

hosts = defaultdict(list)

with open(source, newline="") as f:
    for row in csv.DictReader(f):
        hosts[row["host"]].append(row)

if not hosts:
    raise SystemExit("No benchmark data found in " + source)

summary = []

for host, rows in sorted(hosts.items()):
    rows.sort(key=lambda r: r["timestamp"])

    start = datetime.fromisoformat(rows[0]["timestamp"])
    end = datetime.fromisoformat(rows[-1]["timestamp"])
    duration = max((end - start).total_seconds(), 1)

    avg_cpu = sum(float(r["cpu_percent"]) for r in rows) / len(rows)
    avg_memory = sum(float(r["memory_percent"]) for r in rows) / len(rows)

    packets = int(rows[-1]["packets_received"]) - int(rows[0]["packets_received"])
    avg_rate = max(packets, 0) / duration

    summary.append({
        "host": host,
        "samples": len(rows),
        "average_cpu_percent": round(avg_cpu, 2),
        "average_memory_percent": round(avg_memory, 2),
        "average_packet_rate_pps": round(avg_rate, 3),
        "packets_received": int(rows[-1]["packets_received"])
    })

with open("results/performance_summary.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=summary[0].keys())
    writer.writeheader()
    writer.writerows(summary)

labels = [r["host"] for r in summary]

def save_chart(values, title, ylabel, filename):
    plt.figure(figsize=(9, 5))
    plt.bar(labels, values)
    plt.title(title)
    plt.xlabel("Mininet Host")
    plt.ylabel(ylabel)
    plt.tight_layout()
    plt.savefig("results/" + filename, dpi=150)
    plt.close()

save_chart(
    [r["average_cpu_percent"] for r in summary],
    "Average CPU Utilization", "CPU (%)", "cpu_performance.png"
)

save_chart(
    [r["average_memory_percent"] for r in summary],
    "Average Memory Utilization", "Memory (%)", "memory_performance.png"
)

save_chart(
    [r["average_packet_rate_pps"] for r in summary],
    "Average Telemetry Reception Rate", "Packets per second",
    "packet_rate.png"
)

print("\nPERFORMANCE SUMMARY")
print("=" * 65)
for row in summary:
    print(row)

print("\nGenerated files:")
print("results/performance_summary.csv")
print("results/cpu_performance.png")
print("results/memory_performance.png")
print("results/packet_rate.png")
