import socket
import json
import time
import psutil
import argparse
import platform

parser = argparse.ArgumentParser()
parser.add_argument("--host", required=True)
parser.add_argument("--receiver", default="10.0.0.100")
parser.add_argument("--port", type=int, default=9999)
args = parser.parse_args()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sequence = 0

print(f"Telemetry agent started on {args.host}")
print(f"Sending telemetry to {args.receiver}:{args.port}")

while True:
    sequence += 1

    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory().percent
    network = psutil.net_io_counters()

    telemetry = {
        "host": args.host,
        "sequence": sequence,
        "timestamp": time.time(),
        "cpu_usage": cpu,
        "memory_usage": memory,
        "bytes_sent": network.bytes_sent,
        "bytes_received": network.bytes_recv,
        "platform": platform.system()
    }

    message = json.dumps(telemetry)

    sock.sendto(
        message.encode(),
        (args.receiver, args.port)
    )

    print(f"Sent telemetry #{sequence} | CPU: {cpu}% | Memory: {memory}%")

    time.sleep(4)

