from typing import Optional, Any, Dict, List
from fastmcp import FastMCP
from apis.wttrin.client import WttrInClient
from apis.google_calendar import GoogleCalendarClient


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



@mcp.tool(
    name="list_calendar_events",
    description=(
        "Lists Google Calendar events within the specified time range. "
        "Supports essential optional parameters of the Google Calendar API Events.list. "
        "See: https://developers.google.com/calendar/api/v3/reference/events/list"
    ),
)
async def list_calendar_events(
    calendar_id: str = "primary",
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
    max_results: Optional[int] = None,
    q: Optional[str] = None,
    single_events: bool = True,
    order_by: Optional[str] = "startTime",
) -> Dict[str, Any]:
    """
    Lists events from a Google Calendar within the specified time window.

    Args:
        calendar_id: The calendar ID (default: 'primary').
        time_min: The start time (RFC3339, e.g. '2025-11-17T09:00:00Z').
        time_max: The end time (RFC3339, e.g. '2025-11-17T17:00:00Z').
        max_results: Maximum number of events to return.
        q: Search query to filter events by text.
        single_events: If True, recurring events are returned as individual instances.
        order_by: Sorting field ('startTime' or 'updated').
    """
    try:
        client = GoogleCalendarClient()
        return await client.list_events(
            calendar_id=calendar_id,
            time_min=time_min,
            time_max=time_max,
            max_results=max_results,
            q=q,
            single_events=single_events,
            order_by=order_by,
        )
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}



@mcp.tool(
    name="create_calendar_event",
    description=(
        "Creates a Google Calendar event. "
        "See: https://developers.google.com/calendar/api/v3/reference/events/insert"
    ),
)
async def create_calendar_event(
    calendar_id: str,
    start: str,
    end: str,
    max_attendees: Optional[int] = None,
    send_updates: Optional[str] = None,
    summary: str = "untitled event",
    timezone: Optional[str] = None,
    description: Optional[str] = None,
    location: Optional[str] = None,
    attendees: Optional[List[Dict[str, Any]]] = None,
    all_day: bool = False,
    color_id: Optional[str] = None,
    recurrence: Optional[List[str]] = None,
    reminders: Optional[Dict[str, Any]] = None,
    transparency: Optional[str] = None,
    visibility: Optional[str] = None,
    guests_can_invite_others: Optional[bool] = None,
    guests_can_modify: Optional[bool] = None,
    guests_can_see_other_guests: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Creates an event in the specified Google Calendar.

    Args:
        calendar_id: The ID of the calendar where the event will be created.
        start: Event start time (RFC3339 dateTime string or 'YYYY-MM-DD' for all-day events).
        end: Event end time (RFC3339 dateTime string or 'YYYY-MM-DD' for all-day events).
        max_attendees: Maximum number of attendees returned in the response.
        send_updates: Guest notification behavior ('all', 'externalOnly', 'none').
        summary: Title of the event.
        timezone: IANA timezone name (e.g., 'Europe/Berlin').
        description: Long text description of the event.
        location: Human-readable location string.
        attendees: List of attendee objects. Each object may include:
            - email (required)
            - displayName
            - optional
            - comment
            - additionalGuests
        all_day: True if this is an all-day event (uses date-only format).
        color_id: Optional color ID (1-11).
        recurrence: List of recurrence rules (RRULE, EXRULE, RDATE, EXDATE).
        reminders: Reminder configuration; either useDefault or custom overrides.
        transparency: Whether the event blocks calendar time ('opaque' or 'transparent').
        visibility: Visibility settings ('default', 'public', 'private', 'confidential').
        guests_can_invite_others: Whether guests are allowed to invite additional attendees.
        guests_can_modify: Whether guests are allowed to modify the event.
        guests_can_see_other_guests: Whether guests can view other attendees.
    """
    try:
        client = GoogleCalendarClient()
        return await client.create_event(
            calendar_id=calendar_id,
            start=start,
            end=end,
            max_attendees=max_attendees,
            send_updates=send_updates,
            summary=summary,
            timezone=timezone,
            description=description,
            location=location,
            attendees=attendees,
            all_day=all_day,
            color_id=color_id,
            recurrence=recurrence,
            reminders=reminders,
            transparency=transparency,
            visibility=visibility,
            guests_can_invite_others=guests_can_invite_others,
            guests_can_modify=guests_can_modify,
            guests_can_see_other_guests=guests_can_see_other_guests,
        )
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}



@mcp.tool(
    name="get_calendar_list",
    description=(
        "Lists all Google Calendars of the user. "
        "Supports optional filter parameters such as max_results, min_access_role, page_token, show_deleted, show_hidden, and sync_token. "
        "See: https://developers.google.com/calendar/api/v3/reference/calendarList/list"
    ),
)
async def get_calendar_list(
    max_results: Optional[int] = None,
    min_access_role: Optional[str] = None,
    page_token: Optional[str] = None,
    show_deleted: Optional[bool] = None,
    show_hidden: Optional[bool] = None,
    sync_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Lists all calendars of the user.

    Args:
        max_results: Maximum number of calendars to return.
        min_access_role: Minimum access role required ('freeBusyReader', 'reader', 'writer', 'owner').
        page_token: Token used for pagination.
        show_deleted: Whether to include deleted calendars in the response.
        show_hidden: Whether to include hidden calendars.
        sync_token: Token for incremental synchronization.
    """
    try:
        client = GoogleCalendarClient()
        return await client.get_calendars(
            max_results=max_results,
            min_access_role=min_access_role,
            page_token=page_token,
            show_deleted=show_deleted,
            show_hidden=show_hidden,
            sync_token=sync_token,
        )
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}


if __name__ == "__main__":
    mcp.run()
