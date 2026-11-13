import time
import threading

# Monitoring thresholds
CPU_THRESHOLD = 80
MEMORY_THRESHOLD = 85
TELEMETRY_TIMEOUT = 15

# Shared telemetry data
host_data = {}
alerts = []
active_alerts = set()
lock = threading.Lock()


def process_telemetry(data):
    hostname = data.get("host")
    if not hostname:
        return

    with lock:
        host_data[hostname] = {
            "last_seen": time.time(),
            "cpu": data.get("cpu_usage", 0),
            "memory": data.get("memory_usage", 0),
            "sequence": data.get("sequence", 0)
        }

        # Clear missing telemetry alert when host recovers
        missing_alert = f"MISSING TELEMETRY: {hostname}"
        if missing_alert in active_alerts:
            active_alerts.remove(missing_alert)
            alerts.append(f"RECOVERED: {hostname} telemetry restored")

        # High CPU detection
        cpu_alert = f"HIGH CPU: {hostname}"
        if data.get("cpu_usage", 0) > CPU_THRESHOLD:
            if cpu_alert not in active_alerts:
                active_alerts.add(cpu_alert)
                alerts.append(
                    f"{cpu_alert} at {data['cpu_usage']}%"
                )
        else:
            active_alerts.discard(cpu_alert)

        # High memory detection
        memory_alert = f"HIGH MEMORY: {hostname}"
        if data.get("memory_usage", 0) > MEMORY_THRESHOLD:
            if memory_alert not in active_alerts:
                active_alerts.add(memory_alert)
                alerts.append(
                    f"{memory_alert} at {data['memory_usage']}%"
                )
        else:
            active_alerts.discard(memory_alert)


def detect_missing_hosts():
    while True:
        current_time = time.time()

        with lock:
            for hostname, info in host_data.items():
                if current_time - info["last_seen"] > TELEMETRY_TIMEOUT:
                    alert = f"MISSING TELEMETRY: {hostname}"

                    if alert not in active_alerts:
                        active_alerts.add(alert)
                        alerts.append(alert)

        time.sleep(5)


def get_host_data():
    with lock:
        return dict(host_data)


def get_alerts():
    with lock:
        return list(alerts)


def start_analyzer():
    thread = threading.Thread(
        target=detect_missing_hosts,
        daemon=True
    )
    thread.start()

    print("Telemetry analyzer started")
    print(f"CPU threshold: {CPU_THRESHOLD}%")
    print(f"Memory threshold: {MEMORY_THRESHOLD}%")
    print(f"Missing telemetry timeout: {TELEMETRY_TIMEOUT}s")


if __name__ == "__main__":
    start_analyzer()

    while True:
        time.sleep(10)
        print("\nCurrent host status:", get_host_data())
        print("Alerts:", get_alerts())
