from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

import httpx


@dataclass
class DbTransitClientConfig:
    """
    Configuration for DbTransitClient.
    """
    base_url: str = "https://v6.db.transport.rest"


class DbTransitClient:
    """
    Async client for the DB transport.rest API (v6).

    Documentation:
        https://v6.db.transport.rest/api.html

    Currently used endpoint:
        GET /journeys

    This client focuses on coordinate-based journey planning with optional
    departure/arrival times and localization.
    """

    def __init__(self, config: Optional[DbTransitClientConfig] = None) -> None:
        self.config = config or DbTransitClientConfig()
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """
        Lazily initialize a shared AsyncClient instance.
        """
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=self.config.base_url, timeout=10.0)
        return self._client

    async def aclose(self) -> None:
        """
        Close the underlying HTTP client, if it exists.
        """
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    @staticmethod
    def _isoformat_or_none(value: Optional[str]) -> Optional[str]:
        """
        Validate/normalize an ISO 8601 date-time string for the DB API.

        The DB transport.rest API expects an ISO 8601-like string.
        For robustness, this method:
          - Returns None if value is None.
          - Passes through strings that parse with datetime.fromisoformat.
          - Raises ValueError if parsing fails.
        """
        if value is None:
            return None

        try:
            # This will raise ValueError if the format is invalid.
            dt = datetime.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(
                f"Invalid ISO 8601 datetime string: {value!r}"
            ) from exc

        # Return the ISO string in a normalized form (keep timezone if present).
        return dt.isoformat()

    async def journey_search(
        self,
        origin_lon: float,
        origin_lat: float,
        dest_lon: float,
        dest_lat: float,
        *,
        departure_time: Optional[str] = None,
        arrival_time: Optional[str] = None,
        max_results: int = 5,
        language: str = "de",
        start_with_walking: bool = True,
    ) -> Dict[str, Any]:
        """
        Query the DB transport.rest /journeys endpoint for public transport routes.

        Args:
            origin_lon: Longitude of the origin point.
            origin_lat: Latitude of the origin point.
            dest_lon: Longitude of the destination point.
            dest_lat: Latitude of the destination point.
            departure_time: Optional ISO 8601 date-time string for desired departure.
            arrival_time: Optional ISO 8601 date-time string for desired arrival.
                          Must not be combined with departure_time.
            max_results: Maximum number of journeys to return (DB default is 3).
            language: Language for textual fields (e.g. 'de' or 'en').
            start_with_walking: Whether to include walking from the origin to
                                the first stop (recommended True).

        Returns:
            dict: Parsed JSON response from the /journeys endpoint.

        Raises:
            ValueError: If both departure_time and arrival_time are provided,
                        or if a datetime string is invalid.
            httpx.HTTPError: If the HTTP request fails.
        """
        if max_results <= 0:
            raise ValueError("max_results must be a positive integer.")

        # Validate time arguments
        if departure_time and arrival_time:
            raise ValueError(
                "Only one of departure_time or arrival_time may be provided."
            )

        departure = self._isoformat_or_none(departure_time)
        arrival = self._isoformat_or_none(arrival_time)

        # Build query parameters for /journeys
        # See: https://v6.db.transport.rest/api.html#journeys
        params: Dict[str, Any] = {
            "from.longitude": origin_lon,
            "from.latitude": origin_lat,
            "to.longitude": dest_lon,
            "to.latitude": dest_lat,
            "results": max_results,
            "language": language,
            # ask for walking access/egress legs
            "startWithWalking": str(start_with_walking).lower(),
        }

        if departure is not None:
            params["departure"] = departure
        if arrival is not None:
            params["arrival"] = arrival

        client = await self._get_client()
        response = await client.get("/journeys", params=params)
        response.raise_for_status()
        return response.json()
