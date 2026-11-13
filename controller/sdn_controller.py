import socket
import json
import threading
import ipaddress

from os_ken.base import app_manager
from os_ken.controller import ofp_event
from os_ken.controller.handler import (
    CONFIG_DISPATCHER,
    MAIN_DISPATCHER,
    DEAD_DISPATCHER,
    set_ev_cls
)
from os_ken.ofproto import ofproto_v1_3
from os_ken.lib import hub
from os_ken.lib.packet import packet, ethernet, ether_types


class NetworkMonitorController(app_manager.OSKenApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(NetworkMonitorController, self).__init__(*args, **kwargs)

        self.mac_to_port = {}
        self.datapaths = {}

        self.monitor_thread = hub.spawn(self._monitor)

        self.mitigation_thread = threading.Thread(
            target=self._mitigation_listener,
            daemon=True
        )
        self.mitigation_thread.start()

        self.logger.info(
            "Network Monitoring SDN Controller initialized"
        )

    # Install the default table-miss flow
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):

        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = parser.OFPMatch()

        actions = [
            parser.OFPActionOutput(
                ofproto.OFPP_CONTROLLER,
                ofproto.OFPCML_NO_BUFFER
            )
        ]

        self.add_flow(datapath, 0, match, actions)

        self.logger.info(
            "Switch connected: DPID=%s",
            datapath.id
        )

    # Add a flow entry
    def add_flow(
        self, datapath, priority, match, actions, idle_timeout=0
    ):

        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        instructions = [
            parser.OFPInstructionActions(
                ofproto.OFPIT_APPLY_ACTIONS,
                actions
            )
        ]

        flow_mod = parser.OFPFlowMod(
            datapath=datapath,
            priority=priority,
            match=match,
            instructions=instructions,
            idle_timeout=idle_timeout
        )

        datapath.send_msg(flow_mod)

    # Track connected switches
    @set_ev_cls(
        ofp_event.EventOFPStateChange,
        [MAIN_DISPATCHER, DEAD_DISPATCHER]
    )
    def switch_state_handler(self, ev):

        datapath = ev.datapath

        if ev.state == MAIN_DISPATCHER:
            self.datapaths[datapath.id] = datapath

            self.logger.info(
                "Monitoring switch DPID=%s",
                datapath.id
            )

        elif ev.state == DEAD_DISPATCHER:
            self.datapaths.pop(datapath.id, None)

            self.logger.info(
                "Switch disconnected: DPID=%s",
                datapath.id
            )

    # Learn MAC addresses and forward packets
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):

        msg = ev.msg
        datapath = msg.datapath

        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        dpid = datapath.id
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        if eth is None:
            return

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        dst = eth.dst
        src = eth.src

        self.mac_to_port.setdefault(dpid, {})

        # Learn the source MAC address
        self.mac_to_port[dpid][src] = in_port

        # Find the destination port
        out_port = self.mac_to_port[dpid].get(
            dst,
            ofproto.OFPP_FLOOD
        )

        actions = [
            parser.OFPActionOutput(out_port)
        ]

        # Install a flow for known unicast destinations
        if out_port != ofproto.OFPP_FLOOD:

            match = parser.OFPMatch(
                in_port=in_port,
                eth_dst=dst
            )

            self.add_flow(
                datapath,
                10,
                match,
                actions,
                idle_timeout=30
            )

        # Forward the packet
        data = None

        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions,
            data=data
        )

        datapath.send_msg(out)

    # Periodically request switch statistics
    def _monitor(self):

        while True:

            for datapath in list(self.datapaths.values()):
                self.request_stats(datapath)

            hub.sleep(10)

    def request_stats(self, datapath):

        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        # Request flow statistics
        flow_request = parser.OFPFlowStatsRequest(
            datapath,
            0,
            ofproto.OFPTT_ALL,
            ofproto.OFPP_ANY,
            ofproto.OFPG_ANY,
            0,
            0
        )

        datapath.send_msg(flow_request)

        # Request port statistics
        port_request = parser.OFPPortStatsRequest(
            datapath,
            0,
            ofproto.OFPP_ANY
        )

        datapath.send_msg(port_request)

    # Receive flow statistics
    @set_ev_cls(
        ofp_event.EventOFPFlowStatsReply,
        MAIN_DISPATCHER
    )
    def flow_stats_handler(self, ev):

        datapath = ev.msg.datapath

        for flow in ev.msg.body:

            if flow.priority > 0:

                self.logger.info(
                    "FLOW STATS | Switch=%s | Packets=%s | Bytes=%s | Match=%s",
                    datapath.id,
                    flow.packet_count,
                    flow.byte_count,
                    flow.match
                )

    # Receive port statistics
    @set_ev_cls(
        ofp_event.EventOFPPortStatsReply,
        MAIN_DISPATCHER
    )
    def port_stats_handler(self, ev):

        datapath = ev.msg.datapath

        for port in ev.msg.body:

            self.logger.info(
                "PORT STATS | Switch=%s | Port=%s | RX bytes=%s | TX bytes=%s | RX packets=%s | TX packets=%s",
                datapath.id,
                port.port_no,
                port.rx_bytes,
                port.tx_bytes,
                port.rx_packets,
                port.tx_packets
            )

    # Listen for mitigation commands over TCP
    def _mitigation_listener(self):

        server = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        server.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )

        try:
            server.bind(("127.0.0.1", 9998))
            server.listen(5)

            self.logger.info(
                "Mitigation listener active on TCP port 9998"
            )

            while True:
                conn, address = server.accept()

                with conn:
                    try:
                        data = conn.recv(1024)
                        command = json.loads(data.decode())

                        if command.get("action") == "block":
                            self.block_host(
                                command.get("ip"),
                                command.get("duration", 30)
                            )
                            conn.sendall(b"Mitigation command processed")

                        else:
                            conn.sendall(b"Unknown action")

                    except Exception as error:
                        self.logger.error(
                            "Mitigation command error: %s",
                            error
                        )
                        conn.sendall(b"Mitigation command failed")

        except OSError as error:
            self.logger.error(
                "Mitigation listener could not start: %s",
                error
            )

        finally:
            server.close()

    # Install temporary drop rules on connected switches
    def block_host(self, ip, duration=30):

        try:
            ip = str(ipaddress.ip_address(ip))
            duration = int(duration)

            if not 1 <= duration <= 300:
                raise ValueError(
                    "Duration must be between 1 and 300 seconds"
                )

        except (ValueError, TypeError) as error:
            self.logger.error(
                "Invalid mitigation request: %s",
                error
            )
            return

        if not self.datapaths:
            self.logger.warning(
                "Mitigation failed: no switches connected"
            )
            return

        for datapath in list(self.datapaths.values()):

            parser = datapath.ofproto_parser

            match = parser.OFPMatch(
                eth_type=0x0800,
                ipv4_src=ip
            )

            # Empty instructions mean DROP the matching packets
            flow_mod = parser.OFPFlowMod(
                datapath=datapath,
                priority=100,
                match=match,
                instructions=[],
                hard_timeout=duration
            )

            datapath.send_msg(flow_mod)

            self.logger.warning(
                "MITIGATION | Blocking source IP=%s | Switch=%s | Duration=%ss",
                ip,
                datapath.id,
                duration
            )
