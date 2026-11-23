"""Linux router implementation for Mininet namespaces."""

from __future__ import annotations

from mininet.node import Node


_COMMAND_RC_MARKER = "__LINUX_ROUTER_RC__"


def _run_checked(node: Node, command: str, *, context: str) -> None:
    """Run a command in the router namespace and verify its exit status."""
    wrapped = (
        f"{command} 2>&1; rc=$?; "
        f"printf '\\n{_COMMAND_RC_MARKER}%s' \"$rc\""
    )
    output = node.cmd(wrapped)

    if not isinstance(output, str):
        raise RuntimeError(
            f"Could not determine command status while {context}: "
            "the command returned a non-text result."
        )

    marker_position = output.rfind(_COMMAND_RC_MARKER)
    if marker_position < 0:
        raise RuntimeError(
            f"Could not determine command status while {context}: {output}"
        )

    status_text = output[marker_position + len(_COMMAND_RC_MARKER):].strip()
    try:
        return_code = int(status_text)
    except ValueError as exc:
        raise RuntimeError(
            f"Could not determine command status while {context}: {output}"
        ) from exc

    if return_code != 0:
        command_output = output[:marker_position].strip()
        raise RuntimeError(
            f"Failed while {context} (exit {return_code}): {command_output}"
        )


class LinuxRouter(Node):
    """A Mininet node with independently configurable IPv4/IPv6 forwarding."""

    def config(
        self,
        ipv4_forwarding: bool = False,
        ipv6_forwarding: bool = False,
        **params,
    ):
        if not isinstance(ipv4_forwarding, bool):
            raise TypeError("ipv4_forwarding must be a boolean.")
        if not isinstance(ipv6_forwarding, bool):
            raise TypeError("ipv6_forwarding must be a boolean.")

        result = super().config(**params)

        _run_checked(
            self,
            f"sysctl -w net.ipv4.ip_forward={int(ipv4_forwarding)}",
            context="configuring IPv4 forwarding",
        )
        _run_checked(
            self,
            "sysctl -w "
            f"net.ipv6.conf.all.forwarding={int(ipv6_forwarding)}",
            context="configuring global IPv6 forwarding",
        )
        _run_checked(
            self,
            "sysctl -w "
            f"net.ipv6.conf.default.forwarding={int(ipv6_forwarding)}",
            context="configuring default IPv6 forwarding",
        )

        return result
