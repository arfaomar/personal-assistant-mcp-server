from __future__ import annotations
"""
Asynchronous HTTP mocks and fixtures for db_transit usability tests.

This module provides:
- MockResponse: minimal httpx-like response object
- MockAsyncClient: async HTTP client that returns predefined responses
- mock_client_factory: fixture to create configured MockAsyncClient instances
- patch_db_client: fixture to patch DbTransitClient._get_client with a mock
"""

from typing import Any, Dict, Tuple, Callable, Optional

import httpx
import pytest


RequestKey = Tuple[str, Tuple[Tuple[str, Any], ...]]


class MockResponse:
    """
    Minimal response object emulating the subset of httpx Response used in tests.

    - Stores a status code and JSON payload
    - Raises HTTPStatusError for 4xx/5xx codes when raise_for_status is called
    """

    def __init__(self, status_code: int = 200, json_data: Any | None = None) -> None:
        """
        Initialize a mock response.

        Args:
            status_code: HTTP status code to emulate.
            json_data: JSON-serializable payload returned by json().
        """
        self._status_code = status_code
        self._json_data = json_data

    def raise_for_status(self) -> None:
        """
        Raise httpx.HTTPStatusError for non-success status codes (>= 400).
        """
        if self._status_code >= 400:
            # Minimal error raising for parity with httpx
            raise httpx.HTTPStatusError("Mock HTTP error", request=None, response=None)

    def json(self) -> Any:
        """
        Return the pre-configured JSON payload.
        """
        return self._json_data


class MockAsyncClient:
    """
    Minimal asynchronous HTTP client returning predefined responses per (path, sorted params).

    Useful for network-free usability tests where we assert parameter construction and routing.
    """

    def __init__(self, routes: Dict[RequestKey, Any]) -> None:
        """
        Create a mock async client with a static route table.

        Args:
            routes: Mapping from request keys to JSON payloads.
                    Key shape: (path: str, sorted tuple of (key, value) pairs as strings).
        """
        self._routes = routes
        self.last_request: Optional[Dict[str, Any]] = None

    @staticmethod
    def _key(path: str, params: Dict[str, Any]) -> RequestKey:
        """
        Build a normalized request key from path and params for stable lookup.

        - Sorts parameter items by key
        - Casts all values to str for robust equality
        """
        norm_items = tuple(sorted((k, str(v)) for k, v in (params or {}).items()))
        return (path, norm_items)

    async def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> MockResponse:
        """
        Emulate an async GET request.

        Records the last request (method/path/params) and returns the configured response
        for the normalized request key. Defaults to empty JSON if no route is found.
        """
        params = params or {}
        self.last_request = {"method": "GET", "path": path, "params": params}
        key = self._key(path, params)
        data = self._routes.get(key)
        if data is None:
            return MockResponse(200, {})
        return MockResponse(200, data)

    async def aclose(self) -> None:
        """
        Close the mock client (no-op).
        """
        return None


@pytest.fixture
def mock_client_factory() -> Callable[[Dict[RequestKey, Any]], MockAsyncClient]:
    """
    Fixture returning a factory to create a MockAsyncClient with a given route table.

    Returns:
        Callable that accepts a route mapping and returns a configured MockAsyncClient.
    """
    def _factory(routes: Dict[RequestKey, Any]) -> MockAsyncClient:
        return MockAsyncClient(routes)

    return _factory


@pytest.fixture
def patch_db_client(monkeypatch, mock_client_factory):
    """
    Fixture that patches DbTransitClient._get_client to return a configured mock client.

    Usage:
        mock = patch_db_client({ ("/path", (("k","v"), ...)): {...} })

    Returns:
        Callable that, when invoked with a route table, installs the mock and returns it.
    """
    from apis.db_transit.client import DbTransitClient

    def _patch(routes: Dict[RequestKey, Any]) -> MockAsyncClient:
        """
        Install a MockAsyncClient for DbTransitClient instances and return the mock.

        Args:
            routes: Route mapping used by the mock client.
        """
        mock = mock_client_factory(routes)

        async def _get_client(self) -> MockAsyncClient:  # type: ignore[override]
            return mock

        monkeypatch.setattr(DbTransitClient, "_get_client", _get_client, raising=True)
        return mock

    return _patch
