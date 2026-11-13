# Network Monitoring and Alert System using SDN and Socket Programming

## 1. Project Overview

This project implements a centralized network monitoring and alert system using Software-Defined Networking (SDN), Mininet, Python socket programming, and OpenFlow.

The system monitors six virtual network hosts connected through three Open vSwitches. Each host runs a telemetry agent that periodically sends CPU, memory, and network information to a centralized UDP receiver.

A monitoring analyzer processes the incoming telemetry, detects abnormal conditions, and generates alerts. An SDN controller collects switch statistics and supports dynamic traffic blocking through temporary OpenFlow rules.

A Flask-based web dashboard displays host status, resource utilization, and monitoring alerts in real time.

## 2. Key Features

- Six-host, three-switch Mininet network topology.
- UDP-based host telemetry collection.
- Centralized telemetry receiver.
- CPU and memory threshold monitoring.
- Missing-host telemetry detection.
- Recovery detection when telemetry resumes.
- OpenFlow 1.3 SDN controller.
- Periodic switch flow and port statistics collection.
- Dynamic host blocking through temporary SDN drop rules.
- Flask-based live monitoring dashboard.
- Performance measurement and graphical analysis.
- CSV-based performance reports.

## 3. Network Architecture

The network uses a loop-free tree topology:

```text
             h1       h2
               \     /
                 s1
                /  \
              s2    s3
             / \    / \
            h3  h4  h5  h6
```

### Host IP Addresses

| Host | IP Address |
|---|---|
| h1 | 10.0.0.1 |
| h2 | 10.0.0.2 |
| h3 | 10.0.0.3 |
| h4 | 10.0.0.4 |
| h5 | 10.0.0.5 |
| h6 | 10.0.0.6 |

## 4. Technologies and Protocols

| Technology / Protocol | Purpose |
|---|---|
| Python | Main implementation language |
| UDP | Host telemetry transmission |
| TCP | Dynamic mitigation command communication |
| OpenFlow 1.3 | SDN control and switch statistics |
| Mininet | Virtual network emulation |
| Open vSwitch | Software-defined switches |
| OS-Ken | SDN controller framework |
| ICMP | Network connectivity testing |
| Flask | Web dashboard |
| Matplotlib | Performance graphs |
| CSV | Performance data storage |

### Important Ports

| Port | Purpose |
|---|---|
| 6653 | OpenFlow controller connection |
| 9999 | UDP telemetry receiver |
| 9998 | TCP mitigation listener |
| 5000 | Flask dashboard |

## 5. Project Structure

```text
network-monitoring/
│
├── agents/
│   └── telemetry_agent.py
│
├── controller/
│   └── sdn_controller.py
│
├── monitoring/
│   ├── receiver.py
│   ├── analyzer.py
│   ├── performance.py
│   └── analyze_results.py
│
├── topology/
│   └── network_topology.py
│
├── dashboard/
│   ├── app.py
│   ├── templates/
│   │   └── index.html
│   └── static/
│       └── style.css
│
├── testing/
├── logs/
├── results/
│
├── requirements.txt
├── README.md
└── PROJECT_BUILD_AND_TEST_GUIDE.md
```

## 6. Installation

### Prerequisites

- Ubuntu Linux
- Python 3.10
- Mininet
- Open vSwitch
- Python virtual environment

### Install Python Dependencies

```bash
cd ~/network-monitoring
python3.10 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## 7. Running the Project

The project requires separate terminal sessions for the controller, Mininet topology, telemetry receiver, telemetry agents, and dashboard.

Start the SDN controller first, then launch the Mininet topology. Start the UDP receiver inside the Mininet h1 namespace, followed by the telemetry agents on the six hosts.

Finally, start the Flask dashboard and open:

```text
http://127.0.0.1:5000
```

Refer to **PROJECT_BUILD_AND_TEST_GUIDE.md** for the complete startup commands, terminal arrangement, configuration, troubleshooting, and testing instructions.

## 8. Testing and Evaluation

The implemented system has been tested for:

- Host-to-host connectivity using Mininet ping tests.
- UDP telemetry reception from all six hosts.
- CPU threshold alert generation.
- Memory threshold alert generation.
- Missing telemetry detection.
- Recovery detection after telemetry resumes.
- OpenFlow flow and port statistics collection.
- Dynamic SDN host blocking using temporary drop rules.
- Live dashboard updates.
- Performance data collection and graphical analysis.

Performance results are stored in the `results/` directory.

Generated outputs include:

- `performance_metrics.csv`
- `performance_summary.csv`
- `cpu_performance.png`
- `memory_performance.png`
- `packet_rate.png`

## 9. Implementation Scope

The current implementation includes CPU and memory threshold alerts, missing telemetry detection, recovery notifications, switch statistics monitoring, and dynamic host blocking.

Dedicated port-scanning and flooding detection algorithms are not currently implemented.

## 10. Detailed Documentation

For the complete project development history, environment configuration, commands, debugging procedures, test cases, and performance evaluation, refer to:

**PROJECT_BUILD_AND_TEST_GUIDE.md**
