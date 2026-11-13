
#!/usr/bin/env python3

"""
Network Monitoring and Alert System
Topology: 6 Hosts + 3 Switches

Architecture:
       s1
      /  \
     s2  s3

Two hosts connected to each switch.
OpenFlow version: 1.3
"""

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSSwitch, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel, info

class NetworkMonitoringTopo(Topo):

    def build(self):

        info("*** Creating switches\n")

        s1 = self.addSwitch(
            's1',
            protocols='OpenFlow13',
            failMode='secure'
        )

        s2 = self.addSwitch(
            's2',
            protocols='OpenFlow13',
            failMode='secure'
        )

        s3 = self.addSwitch(
            's3',
            protocols='OpenFlow13',
            failMode='secure'
        )

        info("*** Creating hosts\n")

        h1 = self.addHost('h1', ip='10.0.0.1/24')
        h2 = self.addHost('h2', ip='10.0.0.2/24')

        h3 = self.addHost('h3', ip='10.0.0.3/24')
        h4 = self.addHost('h4', ip='10.0.0.4/24')

        h5 = self.addHost('h5', ip='10.0.0.5/24')
        h6 = self.addHost('h6', ip='10.0.0.6/24')

        info("*** Connecting hosts to switches\n")

        self.addLink(h1, s1)
        self.addLink(h2, s1)

        self.addLink(h3, s2)
        self.addLink(h4, s2)

        self.addLink(h5, s3)
        self.addLink(h6, s3)

        info("*** Connecting switches (loop-free tree)\n")

        self.addLink(s1, s2)
        self.addLink(s1, s3)

def run_network():

    topo = NetworkMonitoringTopo()

    net = Mininet(
        topo=topo,
        switch=OVSSwitch,
        controller=None,
        autoSetMacs=True,
        autoStaticArp=True
    )

    net.addController(
        'c0',
        controller=RemoteController,
        ip='127.0.0.1',
        port=6653
    )

    try:

        info("\n*** Starting network\n")
        net.start()

        info("*** Network started successfully\n")

        info("*** Testing host connectivity\n")
        net.pingAll()

        info("\n*** Network is ready\n")
        info("*** Entering Mininet CLI\n")

        CLI(net)

    finally:

        info("*** Stopping network\n")
        net.stop()

if __name__ == '__main__':

    setLogLevel('info')
    run_network()
