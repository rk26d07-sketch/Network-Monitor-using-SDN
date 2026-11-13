# Network Monitoring and Alert System using SDN and Socket Programming

## Build, Configuration, Debugging and Test Guide

**Environment:** Ubuntu VM, Mininet 2.3.0, Open vSwitch 3.7.1, Python
3.10 virtual environment, OS-Ken 3.1.1, Flask 3.1.3\
**Project directory:** `~/network-monitoring`\
**Topology:** six Mininet hosts and three Open vSwitches, connected as a
loop-free tree\
**Protocols:** UDP telemetry, OpenFlow 1.3 control/statistics, ICMP
connectivity checks, HTTP dashboard

------------------------------------------------------------------------

## 1. Project overview

This project monitors a small software-defined network. Each Mininet
host runs a Python telemetry agent. Agents send periodic UDP messages to
a centralized receiver. The receiver passes measurements to an analyzer,
which tracks host status and creates alerts. An OS-Ken SDN controller
communicates with Open vSwitches using OpenFlow 1.3, learns MAC
addresses, and polls flow and port statistics. A Flask dashboard
displays the latest telemetry and alert history. A separate TCP control
listener accepts a mitigation request and installs temporary drop flows
for a specified IPv4 source address.

### Implemented capabilities

-   Six Mininet hosts and three Open vSwitches.
-   OpenFlow 1.3 controller connection and table-miss handling.
-   MAC learning and basic host connectivity.
-   Periodic flow and port statistics polling by the controller.
-   UDP telemetry with host address, sequence number, timestamp, CPU,
    memory, and network counters.
-   Central UDP receiver on port `9999`.
-   High CPU, high memory, and missing-telemetry alerts, including
    recovery notification.
-   Flask dashboard on port `5000`, refreshed by browser polling.
-   TCP mitigation listener on `127.0.0.1:9998`.
-   Temporary source-IP drop rules with a configurable hard timeout.
-   CSV performance measurements and three generated graphs.

**Scope note:** CPU and memory readings from Mininet hosts may reflect
the shared Ubuntu VM because Mininet network namespaces do not
independently isolate CPU and memory resources. Treat these as
agent-reported measurements in the emulated environment, not six
separate physical-machine resource measurements.

**Detection scope note:** The implemented analyzer covers high CPU, high
memory, and missing telemetry. Do not claim that port scanning or
UDP-flood detection is implemented unless those detectors are added and
separately tested. The mitigation mechanism can block a specified source
IP, but it does not by itself classify traffic as a scan or flood.

------------------------------------------------------------------------

## 2. Architecture and topology

### Data flow

1.  `agents/telemetry_agent.py` collects host metrics.
2.  Agents send JSON telemetry over UDP to `10.0.0.1:9999`.
3.  The receiver runs in host `h1` and calls `monitoring/analyzer.py`.
4.  The receiver writes the latest dashboard state to
    `logs/dashboard_data.json`.
5.  The Flask application reads that file and serves the dashboard and
    `/api/status`.
6.  The OS-Ken controller connects to the three OVS switches using
    OpenFlow 1.3 and polls flow/port statistics.
7.  A TCP request to `127.0.0.1:9998` asks the controller to install a
    temporary source-IP drop rule.

### Loop-free topology

``` text
                 h1       h2
                   \     /
                     s1
                    /  \
                  s2    s3
                 / \    / \
                h3  h4  h5  h6
```

  Host   IPv4 address   Connected switch
  ------ -------------- ------------------
  h1     10.0.0.1/24    s1
  h2     10.0.0.2/24    s1
  h3     10.0.0.3/24    s2
  h4     10.0.0.4/24    s2
  h5     10.0.0.5/24    s3
  h6     10.0.0.6/24    s3

Links: h1-s1, h2-s1, h3-s2, h4-s2, h5-s3, h6-s3, s1-s2, and s1-s3.

The loop-free tree is intentional. An earlier triangle topology caused a
Layer-2 broadcast loop and VM instability. Do not restore the triangle
for the normal demo.

### Important ports

  Port       Purpose
  ---------- ----------------------------------------------
  TCP 6653   OpenFlow controller connection
  UDP 9999   Host telemetry to receiver
  TCP 9998   Local controller mitigation command listener
  TCP 5000   Flask dashboard

------------------------------------------------------------------------

## 3. Project directory

The working project includes:

``` text
network-monitoring/
├── agents/
│   └── telemetry_agent.py
├── controller/
│   └── sdn_controller.py
├── dashboard/
│   ├── app.py
│   ├── templates/
│   │   └── index.html
│   └── static/
│       └── style.css
├── monitoring/
│   ├── receiver.py
│   ├── analyzer.py
│   ├── performance.py
│   └── analyze_results.py
├── topology/
│   └── network_topology.py
├── testing/
├── logs/
│   └── dashboard_data.json
├── results/
│   ├── performance_metrics.csv
│   ├── performance_summary.csv
│   ├── cpu_performance.png
│   ├── memory_performance.png
│   └── packet_rate.png
├── requirements.txt
└── .venv/
```

Some folders may contain additional files depending on the final
version. The authoritative source is the actual project directory.

------------------------------------------------------------------------

# 4. Build process --- the original nine phases

## Phase 1 --- Environment setup

### 1.1 Install/check system components

The environment used for this project:

-   Ubuntu in Oracle VM VirtualBox
-   Mininet 2.3.0
-   Open vSwitch 3.7.1
-   Python 3.10 virtual environment
-   OS-Ken 3.1.1
-   psutil
-   Flask 3.1.3
-   Matplotlib 3.10.9

Useful checks:

``` bash
lsb_release -a
python3 --version
/usr/bin/python3 --version
mn --version
ovs-vsctl --version
```

### 1.2 Create and activate the virtual environment

``` bash
cd ~/network-monitoring
python3.10 -m venv .venv
source .venv/bin/activate
```

The prompt should begin with `(.venv)`.

Install project packages when setting up a fresh environment:

``` bash
python -m pip install --upgrade pip
python -m pip install os-ken==3.1.1 psutil flask matplotlib
```

Verify imports and versions:

``` bash
python -c "import os_ken; print('OS-Ken import OK')"
python -c "import psutil; print('psutil import OK')"
python -c "import flask; print('Flask:', flask.__version__)"
python -c "import matplotlib; print('Matplotlib:', matplotlib.__version__)"
python -m pip show os-ken
python -m pip show -f os-ken
```

Mininet is launched with the system Python (`/usr/bin/python3`), while
the controller, receiver, agents, dashboard and analysis scripts use the
project's Python 3.10 virtual environment.

### 1.3 Troubleshooting environment issues

If `python` is not found, activate `.venv` first. If the virtual
environment is not active:

``` bash
cd ~/network-monitoring
source .venv/bin/activate
```

If OS-Ken has an import or command problem, inspect the installed
package:

``` bash
python -m pip show os-ken
python -c "import os_ken; print(os_ken.__file__)"
python -c "import os_ken.cmd.manager; print('OS-Ken manager import OK')"
```

The working environment used OS-Ken 3.1.1 after a newer installation
caused a missing-module problem. If reproducing that environment, use
the known-good version:

``` bash
python -m pip install --force-reinstall os-ken==3.1.1
```

If a Python source file has a syntax/indentation problem, compile it:

``` bash
python -m py_compile controller/sdn_controller.py
python -m py_compile monitoring/receiver.py monitoring/analyzer.py
python -m py_compile agents/telemetry_agent.py
python -m py_compile topology/network_topology.py
python -m py_compile dashboard/app.py
```

A successful compile produces no output.

------------------------------------------------------------------------

## Phase 2 --- Create the six-host, three-switch Mininet topology

The topology is implemented in:

``` text
topology/network_topology.py
```

It creates six hosts and three OpenFlow 1.3 switches. Switch links form
a tree: s1 connects to s2 and s3. Each switch uses secure fail mode.

### Start the topology

Open a terminal, then run:

``` bash
cd ~/network-monitoring
sudo /usr/bin/python3 topology/network_topology.py
```

Wait for:

-   Network started successfully
-   Host connectivity test
-   `0% dropped` from `pingAll`
-   `mininet>` prompt

### Mininet connectivity tests

At the `mininet>` prompt:

``` text
nodes
net
dump
pingall
h1 ping -c 3 h2
h1 ping -c 3 h6
h3 ping -c 3 h5
```

Expected result: all six hosts are present and `pingall` reports no
packet loss after the controller has installed forwarding rules.

### Topology troubleshooting

If Mininet or OVS has stale state after an interrupted run, exit Mininet
and use:

``` bash
sudo mn -c
sudo ovs-vsctl show
```

Then restart the controller before restarting the topology. Avoid
creating a Layer-2 triangle; retain the loop-free tree.

------------------------------------------------------------------------

## Phase 3 --- Implement and start UDP telemetry agents

Agent source:

``` text
agents/telemetry_agent.py
```

Each agent sends a JSON UDP message containing:

-   Host IP address
-   Sequence number
-   Unix timestamp
-   CPU usage
-   Memory usage
-   Network bytes sent/received
-   Platform name

Telemetry destination is `10.0.0.1`, UDP port `9999`. The agent samples
CPU using `psutil.cpu_percent(interval=1)` and then sleeps for four
seconds, so the practical interval is approximately five seconds.

### Start all six agents

At the Mininet CLI (`mininet>`), enter these commands:

``` text
h1 /home/ubuntu-b/network-monitoring/.venv/bin/python /home/ubuntu-b/network-monitoring/agents/telemetry_agent.py --host 10.0.0.1 --receiver 10.0.0.1 > /tmp/h1_telemetry.log 2>&1 &
h2 /home/ubuntu-b/network-monitoring/.venv/bin/python /home/ubuntu-b/network-monitoring/agents/telemetry_agent.py --host 10.0.0.2 --receiver 10.0.0.1 > /tmp/h2_telemetry.log 2>&1 &
h3 /home/ubuntu-b/network-monitoring/.venv/bin/python /home/ubuntu-b/network-monitoring/agents/telemetry_agent.py --host 10.0.0.3 --receiver 10.0.0.1 > /tmp/h3_telemetry.log 2>&1 &
h4 /home/ubuntu-b/network-monitoring/.venv/bin/python /home/ubuntu-b/network-monitoring/agents/telemetry_agent.py --host 10.0.0.4 --receiver 10.0.0.1 > /tmp/h4_telemetry.log 2>&1 &
h5 /home/ubuntu-b/network-monitoring/.venv/bin/python /home/ubuntu-b/network-monitoring/agents/telemetry_agent.py --host 10.0.0.5 --receiver 10.0.0.1 > /tmp/h5_telemetry.log 2>&1 &
h6 /home/ubuntu-b/network-monitoring/.venv/bin/python /home/ubuntu-b/network-monitoring/agents/telemetry_agent.py --host 10.0.0.6 --receiver 10.0.0.1 > /tmp/h6_telemetry.log 2>&1 &
```

Check logs from a normal Ubuntu shell:

``` bash
tail -n 10 /tmp/h1_telemetry.log
tail -n 10 /tmp/h6_telemetry.log
```

Check agent processes:

``` bash
sudo ps -eo pid,cmd | grep '[t]elemetry_agent.py'
```

**Important process warning:** Mininet hosts share the VM's PID
namespace. Do not run `pkill -f telemetry_agent.py` from a Mininet host;
it can terminate every agent. To stop one agent, identify its PID from
the main Ubuntu shell and kill only that PID:

``` bash
sudo kill <AGENT_PID>
```

------------------------------------------------------------------------

## Phase 4 --- Start the centralized UDP receiver

Receiver source:

``` text
monitoring/receiver.py
```

The receiver binds to UDP `0.0.0.0:9999`, decodes telemetry JSON, passes
it to the analyzer, prints incoming measurements and alerts, and
updates:

``` text
logs/dashboard_data.json
```

The receiver is run inside h1's network namespace because h1 owns the
telemetry destination address `10.0.0.1`.

### Receiver startup

In the established setup, the receiver was started from a normal Ubuntu
shell using the h1 namespace process ID:

``` bash
sudo mnexec -a <H1_NAMESPACE_PID> /home/ubuntu-b/network-monitoring/.venv/bin/python /home/ubuntu-b/network-monitoring/monitoring/receiver.py
```

Replace `<H1_NAMESPACE_PID>` with the current h1 namespace process ID
from the active Mininet run. Do not reuse an old PID after restarting
Mininet.

The receiver should print:

``` text
NETWORK MONITORING - UDP TELEMETRY RECEIVER
Listening on UDP port 9999...
Waiting for host telemetry...
Telemetry analyzer started
```

Once agents are running, receiver output should show all six IP
addresses, sequence numbers, CPU and memory values, and per-host
received-packet counts.

### Receiver troubleshooting

``` bash
sudo ss -lunp
sudo ps -ef | grep '[r]eceiver.py'
```

The UDP socket exists inside h1's network namespace, so a normal `ss`
command in the main namespace may not show it. That is expected.

Use the current Mininet/h1 namespace PID after every topology restart.
If the receiver reports that port 9999 is already in use, check for an
existing receiver before starting another one.

------------------------------------------------------------------------

## Phase 5 --- SDN controller and OpenFlow statistics

Controller source:

``` text
controller/sdn_controller.py
```

The controller is an OS-Ken application using OpenFlow 1.3. It:

-   Accepts switch connections.
-   Installs a table-miss rule that sends unmatched packets to the
    controller.
-   Learns source MAC addresses and installs forwarding rules.
-   Tracks connected datapaths.
-   Periodically requests flow and port statistics (10-second polling
    interval).
-   Handles the mitigation TCP listener.

### Start the controller

Use a separate Ubuntu terminal:

``` bash
cd ~/network-monitoring
source .venv/bin/activate
export PYTHONPATH="$PWD:$PYTHONPATH"
osken-manager controller.sdn_controller
```

Keep this terminal running.

Expected logs include controller initialization, switch connections for
DPID 1, 2 and 3, and periodic flow/port statistics replies.

### Inspect OVS and OpenFlow

From another Ubuntu terminal:

``` bash
sudo ovs-vsctl show
sudo ovs-ofctl -O OpenFlow13 dump-flows s1
sudo ovs-ofctl -O OpenFlow13 dump-flows s2
sudo ovs-ofctl -O OpenFlow13 dump-flows s3
```

Check that switches are connected to the controller and that flow
entries exist.

### Controller troubleshooting

If the controller cannot import `controller.sdn_controller`, ensure the
current directory and `PYTHONPATH` are correct:

``` bash
cd ~/network-monitoring
source .venv/bin/activate
export PYTHONPATH="$PWD:$PYTHONPATH"
python -c "import controller.sdn_controller; print('Controller import OK')"
```

If switches do not connect, check that the controller is running on TCP
port 6653 and that the topology uses the same controller address/port.

------------------------------------------------------------------------

## Phase 6 --- Analyzer and alert handling

Analyzer source:

``` text
monitoring/analyzer.py
```

Current thresholds:

  Condition                                         Threshold
  ------------------- ---------------------------------------
  High CPU                                   Greater than 80%
  High memory                                Greater than 85%
  Missing telemetry     No telemetry for more than 15 seconds

The analyzer maintains latest host data, alert history, and active-alert
state. Repeated alerts are deduplicated while a condition remains
active. When a missing host sends telemetry again, a recovery event is
recorded.

### Test case 1 --- Normal telemetry

**Procedure:** Start all six agents and the receiver.

**Expected result:** Receiver displays regular telemetry for `10.0.0.1`
through `10.0.0.6`. Dashboard host cards show the hosts online.

### Test case 2 --- High CPU alert

Send a test packet from the h1 namespace to the receiver, simulating
host `10.0.0.3` with CPU at 95%:

``` bash
sudo mnexec -a <H1_NAMESPACE_PID> /home/ubuntu-b/network-monitoring/.venv/bin/python -c 'import socket,json,time; s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); d={"host":"10.0.0.3","sequence":9999,"timestamp":time.time(),"cpu_usage":95,"memory_usage":50,"bytes_sent":1000,"bytes_received":2000,"platform":"Linux"}; s.sendto(json.dumps(d).encode(),("10.0.0.1",9999)); print("Test telemetry sent: CPU=95%")'
```

**Expected result:** Receiver prints an alert similar to:

``` text
HIGH CPU: 10.0.0.3 at 95%
```

### Test case 3 --- High memory alert

``` bash
sudo mnexec -a <H1_NAMESPACE_PID> /home/ubuntu-b/network-monitoring/.venv/bin/python -c 'import socket,json,time; s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); d={"host":"10.0.0.4","sequence":9998,"timestamp":time.time(),"cpu_usage":30,"memory_usage":95,"bytes_sent":1000,"bytes_received":2000,"platform":"Linux"}; s.sendto(json.dumps(d).encode(),("10.0.0.1",9999)); print("Test telemetry sent: Memory=95%")'
```

**Expected result:** Receiver prints:

``` text
HIGH MEMORY: 10.0.0.4 at 95%
```

### Test case 4 --- Missing telemetry

1.  Identify the h6 agent PID from the main Ubuntu shell:

``` bash
sudo ps -eo pid,cmd | grep '[t]elemetry_agent.py'
```

2.  Stop only the process whose command contains `--host 10.0.0.6`:

``` bash
sudo kill <H6_AGENT_PID>
```

3.  Wait longer than 15 seconds (the analyzer checks periodically).

**Expected result:** Receiver reports:

``` text
MISSING TELEMETRY: 10.0.0.6
```

### Test case 5 --- Telemetry recovery

At the Mininet CLI, restart h6's agent:

``` text
h6 /home/ubuntu-b/network-monitoring/.venv/bin/python /home/ubuntu-b/network-monitoring/agents/telemetry_agent.py --host 10.0.0.6 --receiver 10.0.0.1 > /tmp/h6_telemetry.log 2>&1 &
```

**Expected result:** Receiver reports:

``` text
RECOVERED: 10.0.0.6 telemetry restored
```

and h6 telemetry resumes.

### Test case 6 --- Basic network connectivity

At the Mininet CLI:

``` text
pingall
h1 ping -c 3 h6
h3 ping -c 3 h4
```

**Expected result:** No packet loss during normal operation.

------------------------------------------------------------------------

## Phase 7 --- Flask monitoring dashboard

Dashboard files:

``` text
dashboard/app.py
dashboard/templates/index.html
dashboard/static/style.css
```

The Flask app reads `logs/dashboard_data.json` and exposes:

-   `/` --- dashboard page
-   `/api/status` --- JSON status endpoint

### Start the dashboard

Use a separate Ubuntu terminal:

``` bash
cd ~/network-monitoring
source .venv/bin/activate
python dashboard/app.py
```

Open a browser inside the VM:

``` text
http://127.0.0.1:5000
```

The page refreshes its data every two seconds.

### Dashboard checks

In a browser, confirm:

-   Total host count is six once all agents report.
-   Online/offline host counts update.
-   CPU, memory and sequence values are displayed.
-   Alert history includes generated alerts.
-   Stopping h6's agent changes its status after the timeout.
-   Restarting h6's agent restores its online status.

The Flask terminal's repeated `GET /api/status ... 200` messages are
normal polling activity.

### Dashboard/API troubleshooting

``` bash
ls -lh logs/dashboard_data.json
python -m json.tool logs/dashboard_data.json
```

If the dashboard says it is waiting for telemetry, check that the
receiver is running and writing the JSON file. If the browser cannot
connect, verify that Flask is still running on port 5000.

------------------------------------------------------------------------

## Phase 8 --- Dynamic SDN mitigation

The controller includes a TCP listener on `127.0.0.1:9998`. It accepts a
JSON request such as:

``` json
{"action":"block","ip":"10.0.0.6","duration":30}
```

The controller validates the IPv4 address and duration (1--300 seconds),
then installs a high-priority IPv4 source-address drop rule on connected
switches. The rule uses a hard timeout, so it expires automatically.

### Test case 7 --- Temporarily block h6

With the controller and Mininet running, execute from a normal Ubuntu
shell:

``` bash
python3 -c 'import socket,json; s=socket.create_connection(("127.0.0.1",9998),timeout=5); s.sendall(json.dumps({"action":"block","ip":"10.0.0.6","duration":30}).encode()); print(s.recv(1024).decode()); s.close()'
```

**Expected result:**

-   The client receives a success response.
-   Controller logs show a mitigation action for `10.0.0.6`.
-   h6's telemetry is interrupted while the drop rule is active.
-   After approximately 30 seconds, the hard-timeout rule expires and
    telemetry resumes.

Inspect flow rules:

``` bash
sudo ovs-ofctl -O OpenFlow13 dump-flows s1
sudo ovs-ofctl -O OpenFlow13 dump-flows s2
sudo ovs-ofctl -O OpenFlow13 dump-flows s3
```

Look for the higher-priority IPv4 source match and drop action while the
rule is active.

**Safety:** Run this test only in the isolated Mininet lab. Use a short
timeout and a test host. Do not block the receiver's own address
(`10.0.0.1`) during the demonstration.

------------------------------------------------------------------------

## Phase 9 --- Testing, performance evaluation and results

### 9.1 Collect performance measurements

The measurement script is:

``` text
monitoring/performance.py
```

It samples dashboard JSON once per second and writes:

``` text
results/performance_metrics.csv
```

Run it from the project root with the virtual environment active:

``` bash
cd ~/network-monitoring
source .venv/bin/activate
python monitoring/performance.py
```

Let it collect for at least 60 seconds, then press `Ctrl+C` to save and
stop.

### 9.2 Generate summary and graphs

``` bash
python monitoring/analyze_results.py
```

Generated outputs:

``` text
results/performance_summary.csv
results/cpu_performance.png
results/memory_performance.png
results/packet_rate.png
```

View the files:

``` bash
ls -lh results/
```

Open a graph from the Ubuntu desktop:

``` bash
xdg-open results/cpu_performance.png
xdg-open results/memory_performance.png
xdg-open results/packet_rate.png
```

### 9.3 Recorded benchmark run

One completed run contained 63 samples per host (378 host-sample rows in
the raw CSV). The generated summary reported:

  -----------------------------------------------------------------------
  Host               Samples    Average CPU Average memory Average packet
                                        (%)            (%)     rate (pps)
  ----------- -------------- -------------- -------------- --------------
  10.0.0.1                63          44.16          83.20          0.190

  10.0.0.2                63          32.88          83.15          0.206

  10.0.0.3                63          43.28          83.15          0.190

  10.0.0.4                63          44.03          83.19          0.190

  10.0.0.5                63          43.40          83.15          0.190

  10.0.0.6                63          43.80          83.20          0.190
  -----------------------------------------------------------------------

These are measurements from that specific VM run, not universal
performance guarantees. The CPU/memory figures are subject to shared-VM
measurement limitations described earlier. Packet rate is consistent
with agents sending roughly one packet every five seconds.

### 9.4 Additional useful diagnostic commands

``` bash
# Check Python processes
ps -ef | grep -E '[o]sken-manager|[r]eceiver.py|[a]pp.py|[t]elemetry_agent.py'

# Check listening TCP/UDP sockets in the current namespace
sudo ss -lntup

# Check OVS bridges and controller configuration
sudo ovs-vsctl show

# Inspect OpenFlow rules
sudo ovs-ofctl -O OpenFlow13 dump-flows s1

# Validate JSON output
python -m json.tool logs/dashboard_data.json

# Compile all main Python components
python -m py_compile controller/sdn_controller.py monitoring/receiver.py monitoring/analyzer.py monitoring/performance.py monitoring/analyze_results.py agents/telemetry_agent.py topology/network_topology.py dashboard/app.py

# Inspect result files
ls -lh results/
```

### Test-case checklist

  -------------------------------------------------------------------------
  Test                    Procedure                 Expected outcome
  ----------------------- ------------------------- -----------------------
  Topology startup        Start controller, then    Three switches connect
                          Mininet                   

  Connectivity            `pingall`                 No packet loss

  Normal telemetry        Start receiver and six    All six hosts report
                          agents                    

  High CPU                Send synthetic CPU=95     High CPU alert
                          packet                    

  High memory             Send synthetic memory=95  High memory alert
                          packet                    

  Missing telemetry       Stop only h6 agent and    Missing telemetry alert
                          wait \>15s                

  Recovery                Restart h6 agent          Recovery alert and
                                                    telemetry resumes

  Dashboard               Open                      Live host/alert data
                          `http://127.0.0.1:5000`   

  SDN mitigation          Block h6 for 30 seconds   Traffic stops
                                                    temporarily, then
                                                    resumes

  Performance             Collect for 60+ seconds   CSV data saved

  Graph generation        Run analysis script       Summary CSV and three
                                                    PNG graphs
  -------------------------------------------------------------------------

------------------------------------------------------------------------

# 5. Clean startup procedure after a VM reboot

A VM reboot stops running processes, but project files and saved CSV/PNG
results remain on disk.

Use separate terminal tabs for the long-running processes. The order
matters.

### Terminal 1 --- Controller

``` bash
cd ~/network-monitoring
source .venv/bin/activate
export PYTHONPATH="$PWD:$PYTHONPATH"
osken-manager controller.sdn_controller
```

Leave it running.

### Terminal 2 --- Mininet

``` bash
cd ~/network-monitoring
sudo /usr/bin/python3 topology/network_topology.py
```

Wait for `mininet>` and confirm controller switch-connection logs in
Terminal 1.

### Terminal 3 --- Receiver

Start the receiver inside h1's network namespace using the current h1
namespace PID:

``` bash
sudo mnexec -a <CURRENT_H1_NAMESPACE_PID> /home/ubuntu-b/network-monitoring/.venv/bin/python /home/ubuntu-b/network-monitoring/monitoring/receiver.py
```

Leave it running.

### Mininet CLI --- Six agents

Enter the six agent commands from Phase 3 at the `mininet>` prompt.

### Terminal 4 --- Flask dashboard

``` bash
cd ~/network-monitoring
source .venv/bin/activate
python dashboard/app.py
```

Open `http://127.0.0.1:5000`.

### Terminal 5 --- Optional performance collection

``` bash
cd ~/network-monitoring
source .venv/bin/activate
python monitoring/performance.py
```

Stop with `Ctrl+C` after the desired collection period.

**Do not close the controller, Mininet, receiver or Flask terminals
while demonstrating the live system.** If Mininet is restarted, restart
the receiver and agents too, and obtain the new h1 namespace PID.

------------------------------------------------------------------------

# 6. Common problems and fixes

  -----------------------------------------------------------------------------------------------
  Symptom                        Likely cause            Action
  ------------------------------ ----------------------- ----------------------------------------
  `python: command not found`    Virtual environment not `source .venv/bin/activate`; then use
                                 active                  `python`

  `No module named controller`   Project root missing    `export PYTHONPATH="$PWD:$PYTHONPATH"`
                                 from Python path        

  `osken-manager` fails or       Wrong/broken OS-Ken     Verify `python -m pip show os-ken`; use
  OS-Ken import fails            installation            known-good 3.1.1

  Mininet says unknown command   Controller logs were    Read controller logs in the controller
  for controller log text        typed at `mininet>`     terminal, not Mininet CLI

  `pingall` fails                Controller/switch       Check controller, OVS and `sudo mn -c`;
                                 connection or stale     restart in correct order
                                 Mininet state           

  UDP receiver sees no packets   Receiver not running in Check receiver, agent processes and h1
                                 h1 namespace, wrong     address
                                 destination, or agents  
                                 stopped                 

  Port 9999 not visible in main  Receiver socket belongs Expected; inspect from the correct
  `ss` output                    to h1 network namespace namespace

  Dashboard has no data          Receiver not writing    Check receiver output and
                                 dashboard JSON          `logs/dashboard_data.json`

  Dashboard terminal prints      Browser polls API every Normal behavior
  repeated GET requests          two seconds             

  All agents stop after killing  A broad `pkill` was     Restart agents; stop only the exact PID
  one                            used across shared PID  
                                 namespace               

  VM freezes or broadcast        Layer-2 loop in         Keep the loop-free tree topology
  traffic loops                  topology                

  Matplotlib import fails        Package not installed   Activate `.venv`, install Matplotlib,
                                 in active venv          verify import
  -----------------------------------------------------------------------------------------------

------------------------------------------------------------------------

# 7. Demonstration sequence

For a concise live demonstration:

1.  Show the project directory and the topology source.
2.  Start the OS-Ken controller and show three switch connections.
3.  Start Mininet and run `pingall`.
4.  Start the receiver and six telemetry agents.
5.  Open the dashboard and show all six hosts online.
6.  Trigger the synthetic high-CPU and high-memory test packets and show
    alerts.
7.  Stop h6's agent, wait for the missing-telemetry alert, then restart
    it and show recovery.
8.  Send a 30-second mitigation request for h6 and show the controller
    log and temporary interruption/recovery.
9.  Show flow/port statistics and OpenFlow rules.
10. Show the performance CSV, summary CSV, and three generated graphs.

------------------------------------------------------------------------

# 8. Final project files to preserve

Before submission, ensure these are present:

``` text
controller/sdn_controller.py
monitoring/receiver.py
monitoring/analyzer.py
monitoring/performance.py
monitoring/analyze_results.py
agents/telemetry_agent.py
topology/network_topology.py
dashboard/app.py
dashboard/templates/index.html
dashboard/static/style.css
results/performance_metrics.csv
results/performance_summary.csv
results/cpu_performance.png
results/memory_performance.png
results/packet_rate.png
logs/dashboard_data.json
```

Also preserve `requirements.txt` and this guide. Capture screenshots of
the running Mininet topology, controller statistics, receiver telemetry,
dashboard, alerts, mitigation, and performance graphs for the final
report.

**Reproducibility reminder:** Commands containing `<H1_NAMESPACE_PID>`
or `<H6_AGENT_PID>` are placeholders. Replace them with current process
IDs from the current VM/Mininet run; process IDs change after reboot or
topology restart.
