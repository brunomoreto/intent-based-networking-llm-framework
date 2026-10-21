
"""Read-only REST client for the ONOS controller."""

import base64
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class OnosClientError(RuntimeError):
    """Raised when an ONOS REST request fails."""


class OnosClient:
    """Read-only client for the ONOS REST API."""

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        timeout: float = 5.0,
    ) -> None:
        if not base_url.startswith(("http://", "https://")):
            raise ValueError("base_url must use HTTP or HTTPS.")

        if not username or not password:
            raise ValueError("ONOS username and password are required.")

        if timeout <= 0:
            raise ValueError("timeout must be positive.")

        self._base_url = base_url.rstrip("/")
        self._username = username
        self._password = password
        self._timeout = timeout

    def _get_collection(self, endpoint: str, key: str) -> list[dict[str, Any]]:
        credentials = f"{self._username}:{self._password}".encode("utf-8")
        token = base64.b64encode(credentials).decode("ascii")

        request = Request(
            f"{self._base_url}/onos/v1/{endpoint}",
            headers={
                "Authorization": f"Basic {token}",
                "Accept": "application/json",
            },
            method="GET",
        )

        try:
            with urlopen(request, timeout=self._timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise OnosClientError(
                f"ONOS returned HTTP {exc.code} for {endpoint}."
            ) from exc
        except URLError as exc:
            raise OnosClientError(
                f"Could not connect to ONOS for {endpoint}: {exc.reason}"
            ) from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise OnosClientError(
                f"ONOS returned invalid JSON for {endpoint}."
            ) from exc

        if not isinstance(payload, dict):
            raise OnosClientError(
                f"ONOS response for {endpoint} must be a JSON object."
            )

        collection = payload.get(key)
        if not isinstance(collection, list):
            raise OnosClientError(
                f"ONOS response for {endpoint} must contain a '{key}' list."
            )

        if not all(isinstance(item, dict) for item in collection):
            raise OnosClientError(
                f"ONOS '{key}' entries must be JSON objects."
            )

        return collection

    def get_devices(self) -> list[dict[str, Any]]:
        """Return devices currently known to ONOS."""
        return self._get_collection("devices", "devices")

    def get_links(self) -> list[dict[str, Any]]:
        """Return links currently known to ONOS."""
        return self._get_collection("links", "links")

    def get_topology_snapshot(self) -> dict[str, list[dict[str, Any]]]:
        """Return device and link collections from ONOS."""
        return {
            "devices": self.get_devices(),
            "links": self.get_links(),
        }


__all__ = ["OnosClient", "OnosClientError"]
