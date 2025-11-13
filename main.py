from typing import Optional, Any, Dict
from fastmcp import FastMCP
from apis.wttrin.client import WttrInClient


# Initialize the MCP server
mcp = FastMCP("Personal AI Assistant MCP Server")

# Initialize the wttr.in client
wttr = WttrInClient()

@mcp.tool(
    name="get_weather",
    description=(
        "Fetch current and forecast weather data from wttr.in in JSON format (format=j1). "
        "If no location is provided, wttr.in automatically uses your external IP to determine the current location."
    ),
)
async def get_weather(
    location: Optional[str] = None,
    lang: Optional[str] = None,
    unit: Optional[str] = "m",
    forecast_days: Optional[int] = 0,
) -> Dict[str, Any]:
    """
    Get weather data from wttr.in (JSON format, format=j1).

    Args:
        location: City, IATA code, domain, landmark, zip, or coordinates.
            If omitted or empty, wttr.in will automatically detect the user's
            current location based on their external IP address.
        lang: Language code (optional, e.g. 'de', 'fr', 'pt-br').
        unit: Unit system ('m' metric, 'u' USCS, 'M' metric + m/s wind).
        forecast_days: 0, 1, or 2 (forecast range, default 0 = current weather only).
    """
    return await wttr.get_weather(location, lang, unit, forecast_days)


if __name__ == "__main__":
    mcp.run()
