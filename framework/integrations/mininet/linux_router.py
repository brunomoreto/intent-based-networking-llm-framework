
"""Linux Router implementation for Mininet."""

from mininet.node import Node


class LinuxRouter(Node):
    """Linux-based router running inside a Mininet network namespace."""

    def config(
        self,
        ipv4_forwarding: bool = False,
        ipv6_forwarding: bool = False,
        **params,
    ):
        """Configure the router and its IP forwarding capabilities."""

        if not isinstance(ipv4_forwarding, bool):
            raise TypeError("ipv4_forwarding must be a boolean.")

        if not isinstance(ipv6_forwarding, bool):
            raise TypeError("ipv6_forwarding must be a boolean.")

        result = super().config(**params)

        ipv4_value = int(ipv4_forwarding)
        ipv6_value = int(ipv6_forwarding)

        self.cmd(
            f"sysctl -w net.ipv4.ip_forward={ipv4_value}"
        )

        self.cmd(
            f"sysctl -w net.ipv6.conf.all.forwarding={ipv6_value}"
        )

        self.cmd(
            f"sysctl -w net.ipv6.conf.default.forwarding={ipv6_value}"
        )

        return result
