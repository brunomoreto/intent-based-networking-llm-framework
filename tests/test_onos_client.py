
import base64
import json
from io import BytesIO
from unittest.mock import patch
from urllib.error import URLError

import pytest

from framework.services.collector.onos_client import (
    OnosClient,
    OnosClientError,
)


@pytest.fixture
def client():
    return OnosClient(
        base_url="http://onos.example:8181",
        username="test-user",
        password="test-password",
    )


def mock_response(payload):
    return BytesIO(json.dumps(payload).encode("utf-8"))


def test_get_devices_returns_onos_devices(client):
    payload = {"devices": [{"id": "of:0000000000000001"}]}

    with patch(
        "framework.services.collector.onos_client.urlopen",
        return_value=mock_response(payload),
    ):
        assert client.get_devices() == payload["devices"]


def test_get_links_returns_onos_links(client):
    payload = {"links": [{"src": {"device": "of:1"}}]}

    with patch(
        "framework.services.collector.onos_client.urlopen",
        return_value=mock_response(payload),
    ):
        assert client.get_links() == payload["links"]


def test_request_uses_basic_authentication(client):
    payload = {"devices": []}

    with patch(
        "framework.services.collector.onos_client.urlopen",
        return_value=mock_response(payload),
    ) as mocked_urlopen:
        client.get_devices()

    request = mocked_urlopen.call_args.args[0]
    expected = base64.b64encode(
        b"test-user:test-password"
    ).decode("ascii")

    assert request.get_header("Authorization") == f"Basic {expected}"
    assert request.full_url == "http://onos.example:8181/onos/v1/devices"


def test_invalid_response_structure_raises_error(client):
    with patch(
        "framework.services.collector.onos_client.urlopen",
        return_value=mock_response({"unexpected": []}),
    ):
        with pytest.raises(OnosClientError):
            client.get_devices()


def test_connection_error_is_wrapped(client):
    with patch(
        "framework.services.collector.onos_client.urlopen",
        side_effect=URLError("connection refused"),
    ):
        with pytest.raises(OnosClientError):
            client.get_devices()


def test_invalid_credentials_are_rejected():
    with pytest.raises(ValueError):
        OnosClient(
            base_url="http://onos.example:8181",
            username="",
            password="test-password",
        )
