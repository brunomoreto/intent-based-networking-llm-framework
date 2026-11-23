
import os

import pytest

mininet_node = pytest.importorskip("mininet.node")

from mininet.net import Mininet

from framework.integrations.mininet.linux_router import LinuxRouter


@pytest.mark.skipif(
    os.name != "posix" or os.geteuid() != 0,
    reason="LinuxRouter integration test requires Linux root privileges.",
)
def test_linux_router_enables_ipv4_and_ipv6_forwarding():
    net = Mininet(controller=None, build=False)

    try:
        router = net.addHost(
            "r1",
            cls=LinuxRouter,
            ip=None,
            ipv4_forwarding=True,
            ipv6_forwarding=True,
        )

        router.configDefault()

        ipv4_forwarding = router.cmd(
            "sysctl -n net.ipv4.ip_forward"
        ).strip()

        ipv6_forwarding = router.cmd(
            "sysctl -n net.ipv6.conf.all.forwarding"
        ).strip()

        assert ipv4_forwarding == "1"
        assert ipv6_forwarding == "1"

    finally:
        net.stop()
