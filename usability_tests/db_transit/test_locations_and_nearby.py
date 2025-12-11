import pytest

from apis.db_transit.client import DbTransitClient


@pytest.mark.asyncio
async def test_search_locations_validates_inputs():
    """Ensure input validation for empty query and non-positive max_results."""
    client = DbTransitClient()
    with pytest.raises(ValueError):
        await client.search_locations("")
    with pytest.raises(ValueError):
        await client.search_locations("Berlin", max_results=0)


@pytest.mark.asyncio
async def test_search_locations_builds_params_and_calls_correct_endpoint(
    patch_db_client,
):
    """Verify correct /locations parameters and endpoint are used for a query."""
    routes = {
        (
            "/locations",
            (
                ("addresses", "true"),
                ("language", "de"),
                ("poi", "true"),
                ("query", "Berlin"),
                ("results", "5"),
                ("stops", "true"),
            ),
        ): [{"id": "abc", "name": "Berlin Hbf"}]
    }

    client = DbTransitClient()
    mock = patch_db_client(routes)
    data = await client.search_locations("Berlin", max_results=5, language="de")

    assert isinstance(data, list)
    assert mock.last_request is not None
    assert mock.last_request["path"] == "/locations"
    params = mock.last_request["params"]
    assert params["query"] == "Berlin"
    assert params["stops"] == "true"
    assert params["addresses"] == "true"
    assert params["poi"] == "true"


@pytest.mark.asyncio
async def test_find_nearest_stop_returns_first_item(patch_db_client):
    """Confirm the first nearby stop is returned and endpoint is correct."""
    routes = {
        (
            "/locations/nearby",
            (("latitude", "52.5"), ("longitude", "13.4"), ("results", "1")),
        ): [{"id": "stop-1", "name": "Near Stop"}]
    }
    client = DbTransitClient()
    mock = patch_db_client(routes)

    result = await client.find_nearest_stop(lon=13.4, lat=52.5)
    assert result["id"] == "stop-1"
    assert mock.last_request["path"] == "/locations/nearby"


@pytest.mark.asyncio
async def test_find_nearest_stop_raises_if_empty(patch_db_client):
    """Raise ValueError when no nearby stops are returned by the API."""
    routes = {
        (
            "/locations/nearby",
            (("latitude", "0.0"), ("longitude", "0.0"), ("results", "1")),
        ): []
    }
    client = DbTransitClient()
    patch_db_client(routes)

    with pytest.raises(ValueError):
        await client.find_nearest_stop(lon=0.0, lat=0.0)
