import httpx
import re
from datetime import datetime
from typing import Optional, Dict, Any


class WttrInClient:
    """
    Lightweight client for wttr.in using JSON format (format=j1).

    Supports:
      - ?0, ?1, ?2 forecast range flags
      - validated lang, unit, and date
      - only returns JSON
    """

    BASE_URL = "https://wttr.in"

    SUPPORTED_LANGS = {
        "en",
        "am",
        "ar",
        "af",
        "be",
        "bn",
        "ca",
        "da",
        "de",
        "el",
        "et",
        "fr",
        "fa",
        "gl",
        "hi",
        "hu",
        "ia",
        "id",
        "it",
        "lt",
        "mg",
        "nb",
        "nl",
        "oc",
        "pl",
        "pt-br",
        "ro",
        "ru",
        "ta",
        "tr",
        "th",
        "uk",
        "vi",
        "zh-cn",
        "zh-tw",
    }

    SUPPORTED_UNITS = {"m", "u", "M"}  # metric, USCS, metric+m/s
    SUPPORTED_FORECAST_FLAGS = {0, 1, 2}

    def __init__(self):
        self.timeout = 10

    def _validate_lang(self, lang: Optional[str]) -> str:
        if not lang:
            return "en"
        lang = lang.lower()
        if lang not in self.SUPPORTED_LANGS:
            raise ValueError(f"Unsupported language '{lang}'.")
        return lang

    def _validate_unit(self, unit: Optional[str]) -> str:
        if not unit:
            return "m"
        if unit not in self.SUPPORTED_UNITS:
            raise ValueError(
                f"Invalid unit '{unit}'. Must be one of {self.SUPPORTED_UNITS}."
            )
        return unit

    def _validate_date(self, date: Optional[str]) -> Optional[str]:
        if not date:
            return None
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
            raise ValueError("Date must be in YYYY-MM-DD format.")
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Invalid date value.")
        return date

    def _validate_forecast_days(self, forecast_days: Optional[int]) -> int:
        if forecast_days is None:
            return 2  # default 2-day forecast
        if forecast_days not in self.SUPPORTED_FORECAST_FLAGS:
            raise ValueError(
                f"forecast_days must be one of {self.SUPPORTED_FORECAST_FLAGS}."
            )
        return forecast_days

    async def get_weather(
        self,
        location: str,
        lang: Optional[str] = None,
        unit: Optional[str] = None,
        forecast_days: Optional[int] = 0,
    ) -> Dict[str, Any]:
        """
        Get weather data in JSON format (format=j1).

        Args:
            location: city, IATA code, domain, landmark, zip, or coordinates
            lang: one of supported language codes
            unit: one of 'm', 'u', 'M'
            forecast_days: 0, 1, or 2

        Returns:
            dict: Parsed JSON weather data.
        """
        if not location:
            raise ValueError("Location is required.")

        lang = self._validate_lang(lang)
        unit = self._validate_unit(unit)
        forecast_days = self._validate_forecast_days(forecast_days)

        params = {"format": "j1", "lang": lang, unit: "", str(forecast_days): ""}

        url = f"{self.BASE_URL}/{location}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()

    async def get_moon(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get moon phase data (JSON format, format=j1).

        Args:
            date: optional 'YYYY-MM-DD'
        """
        date = self._validate_date(date)
        path = "/moon"
        if date:
            path += f"@{date}"

        params = {"format": "j1"}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(f"{self.BASE_URL}{path}", params=params)
            resp.raise_for_status()
            return resp.json()
