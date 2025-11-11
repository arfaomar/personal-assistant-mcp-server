from typing import Optional, Any, Dict
from fastmcp import FastMCP
from apis.wttrin.client import WttrInClient


# Initialize the MCP server
mcp = FastMCP("Personal AI Assistant MCP Server")


@mcp.tool(
    name="get_weather",
    description="Fetch current and forecast weather data from wttr.in in JSON format (format=j1).",
)
async def get_weather(
    location: str,
    lang: Optional[str] = None,
    unit: Optional[str] = "m",
    forecast_days: Optional[int] = 2,
) -> Dict[str, Any]:
    """
    Get weather data from wttr.in (JSON format).
    Args:
        location: City, IATA code, domain, landmark, zip, or coordinates.
        lang: Language code (optional, e.g. 'de', 'fr', 'pt-br').
        unit: Unit system ('m' metric, 'u' USCS, 'M' metric + m/s wind).
        forecast_days: 0, 1, or 2 (forecast range).
    """
    wttr = WttrInClient()
    data = await wttr.get_weather(location, lang, unit, forecast_days)
    return data


if __name__ == "__main__":
    mcp.run()
