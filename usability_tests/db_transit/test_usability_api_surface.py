import pytest

from apis.db_transit.client import DbTransitClient, DbTransitClientConfig


def test_default_config_base_url():
    """The default base_url should point to DB transport.rest v6 endpoint."""
    cfg = DbTransitClientConfig()
    assert cfg.base_url.startswith("https://v6.db.transport.rest")


@pytest.mark.asyncio
async def test_client_reuses_single_async_client_instance():
    """Ensure the underlying AsyncClient is reused and can be closed/recreated."""
    client = DbTransitClient()
    c1 = await client._get_client()
    c2 = await client._get_client()
    assert c1 is c2
    await client.aclose()
    c3 = await client._get_client()
    assert c3 is not c1


@pytest.mark.asyncio
async def test_isoformat_validator_accepts_valid_and_rejects_invalid():
    """Validate ISO formatting helper for accepted, None, and invalid inputs."""
    client = DbTransitClient()
    assert client._isoformat_or_none("2025-12-03T10:00:00") == "2025-12-03T10:00:00"
    assert client._isoformat_or_none(None) is None
    with pytest.raises(ValueError):
        client._isoformat_or_none("03-12-2025 10:00")


