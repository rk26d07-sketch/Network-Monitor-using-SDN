from flask import Flask, render_template, jsonify
import json
import os
import time

app = Flask(__name__)

DATA_FILE = os.path.expanduser(
    "~/network-monitoring/logs/dashboard_data.json"
)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/status")
def status():
    if not os.path.exists(DATA_FILE):
        return jsonify({
            "status": "waiting",
            "message": "Waiting for telemetry data",
            "hosts": {},
            "alerts": []
        })

    try:
        with open(DATA_FILE, "r") as file:
            data = json.load(file)

        for host, info in data.get("hosts", {}).items():
            info["online"] = (
                time.time() - info.get("last_seen", 0) <= 15
            )

        return jsonify(data)

    except (OSError, json.JSONDecodeError):
        return jsonify({"status": "error", "hosts": {}, "alerts": []})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
