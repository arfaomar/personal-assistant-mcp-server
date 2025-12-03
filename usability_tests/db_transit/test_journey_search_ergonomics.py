import pytest

from apis.db_transit.client import DbTransitClient


@pytest.mark.asyncio
async def test_journey_search_rejects_both_departure_and_arrival():
    """Reject providing both departure and arrival times simultaneously."""
    client = DbTransitClient()
    with pytest.raises(ValueError):
        await client.journey_search(
            origin_lon=13.4,
            origin_lat=52.5,
            dest_lon=13.3,
            dest_lat=52.6,
            departure_time="2025-12-03T10:00:00",
            arrival_time="2025-12-03T11:00:00",
        )


@pytest.mark.asyncio
async def test_journey_search_happy_path_resolves_stops_and_calls_journeys(patch_db_client):
    """Happy path: resolve nearest stops, then call /journeys with proper params."""
    routes = {
        (
            "/locations/nearby",
            (("latitude", "52.5"), ("longitude", "13.4"), ("results", "1")),
        ): [{"id": "o-stop"}],
        (
            "/locations/nearby",
            (("latitude", "52.6"), ("longitude", "13.3"), ("results", "1")),
        ): [{"id": "d-stop"}],
        (
            "/journeys",
            (
                ("departure", "2025-12-03T10:00:00"),
                ("from", "o-stop"),
                ("language", "de"),
                ("results", "3"),
                ("to", "d-stop"),
            ),
        ): {"journeys": [{"id": "j1"}]},
    }

    client = DbTransitClient()
    mock = patch_db_client(routes)

    result = await client.journey_search(
        origin_lon=13.4,
        origin_lat=52.5,
        dest_lon=13.3,
        dest_lat=52.6,
        departure_time="2025-12-03T10:00:00",
        max_results=3,
        language="de",
        start_with_walking=True,
    )

    assert "journeys" in result
    assert mock.last_request is not None
    assert mock.last_request["path"] == "/journeys"
    params = mock.last_request["params"]
    assert params["from"] == "o-stop"
    assert params["to"] == "d-stop"
    assert params["departure"] == "2025-12-03T10:00:00"


