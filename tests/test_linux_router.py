"""Unit and integration tests for the Mininet LinuxRouter."""

import importlib.util
import os
import sys
import types
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LINUX_ROUTER_PATH = (
    PROJECT_ROOT / "framework" / "integrations" / "mininet" / "linux_router.py"
)


class FakeNode:
    """Minimal stand-in for Mininet's Node class."""

    def __init__(self):
        self.commands = []
        self.responses = []
        self.config_params = None

    def config(self, **params):
        self.config_params = params
        return {"configured": True}

    def cmd(self, command):
        self.commands.append(command)
        if self.responses:
            return self.responses.pop(0)
        return "\n__LINUX_ROUTER_RC__0"


@pytest.fixture
def linux_router_module(monkeypatch):
    """Load LinuxRouter against a fake Mininet Node, without Mininet installed."""
    mininet_module = types.ModuleType("mininet")
    node_module = types.ModuleType("mininet.node")
    node_module.Node = FakeNode
    mininet_module.node = node_module

    monkeypatch.setitem(sys.modules, "mininet", mininet_module)
    monkeypatch.setitem(sys.modules, "mininet.node", node_module)

    spec = importlib.util.spec_from_file_location(
        "linux_router_under_test", LINUX_ROUTER_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    ("ipv4_forwarding", "ipv6_forwarding", "expected"),
    [
        (True, True, (1, 1, 1)),
        (False, False, (0, 0, 0)),
        (True, False, (1, 0, 0)),
        (False, True, (0, 1, 1)),
    ],
)
def test_configures_ipv4_and_ipv6_forwarding_independently(
    linux_router_module, ipv4_forwarding, ipv6_forwarding, expected
):
    router = linux_router_module.LinuxRouter()

    result = router.config(
        ipv4_forwarding=ipv4_forwarding,
        ipv6_forwarding=ipv6_forwarding,
        ip=None,
    )

    assert result == {"configured": True}
    assert len(router.commands) == 3
    assert f"net.ipv4.ip_forward={expected[0]}" in router.commands[0]
    assert f"net.ipv6.conf.all.forwarding={expected[1]}" in router.commands[1]
    assert f"net.ipv6.conf.default.forwarding={expected[2]}" in router.commands[2]


@pytest.mark.parametrize(
    ("parameter", "value"),
    [
        ("ipv4_forwarding", 1),
        ("ipv4_forwarding", "true"),
        ("ipv6_forwarding", 0),
        ("ipv6_forwarding", None),
    ],
)
def test_rejects_non_boolean_forwarding_parameters(
    linux_router_module, parameter, value
):
    router = linux_router_module.LinuxRouter()

    with pytest.raises(TypeError, match=f"{parameter} must be a boolean"):
        router.config(**{parameter: value})

    assert router.commands == []
    assert router.config_params is None


@pytest.mark.parametrize("failed_command_index", [0, 1, 2])
def test_raises_when_any_sysctl_command_fails(
    linux_router_module, failed_command_index
):
    router = linux_router_module.LinuxRouter()
    router.responses = ["\n__LINUX_ROUTER_RC__0"] * 3
    router.responses[failed_command_index] = (
        "sysctl: permission denied\n__LINUX_ROUTER_RC__1"
    )

    with pytest.raises(RuntimeError, match="Failed while configuring"):
        router.config(ipv4_forwarding=True, ipv6_forwarding=True)

    assert len(router.commands) == failed_command_index + 1


def test_raises_when_command_status_marker_is_missing(linux_router_module):
    router = linux_router_module.LinuxRouter()
    router.responses = ["sysctl: command unavailable"]

    with pytest.raises(RuntimeError, match="Could not determine command status"):
        router.config(ipv4_forwarding=True, ipv6_forwarding=True)

    assert len(router.commands) == 1


def test_passes_remaining_parameters_to_base_node_config(linux_router_module):
    router = linux_router_module.LinuxRouter()

    router.config(
        ipv4_forwarding=True,
        ipv6_forwarding=False,
        ip=None,
        mac="00:00:00:00:00:01",
    )

    assert router.config_params == {"ip": None, "mac": "00:00:00:00:00:01"}


@pytest.mark.skipif(
    not sys.platform.startswith("linux") or os.geteuid() != 0,
    reason="LinuxRouter integration test requires Linux root privileges.",
)
def test_linux_router_enables_ipv4_and_ipv6_forwarding():
    """Exercise a real Mininet namespace on a privileged Linux host."""
    mininet_node = pytest.importorskip("mininet.node")
    from mininet.net import Mininet

    from framework.integrations.mininet.linux_router import LinuxRouter

    assert issubclass(LinuxRouter, mininet_node.Node)

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

        assert router.cmd("sysctl -n net.ipv4.ip_forward").strip() == "1"
        assert router.cmd(
            "sysctl -n net.ipv6.conf.all.forwarding"
        ).strip() == "1"
        assert router.cmd(
            "sysctl -n net.ipv6.conf.default.forwarding"
        ).strip() == "1"
    finally:
        net.stop()
