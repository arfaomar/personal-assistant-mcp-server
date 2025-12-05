from typing import Optional, Any, Dict, List
import json
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
        q: Free text search terms to find events that match these terms in the following fields:
            summary
            description
            location
            attendee's displayName
            attendee's email
            organizer's displayName
            organizer's email
            workingLocationProperties.officeLocation.buildingId
            workingLocationProperties.officeLocation.deskId
            workingLocationProperties.officeLocation.label
            workingLocationProperties.customLocation.label

            These search terms also match predefined keywords against all display title translations of working location, 
            out-of-office, and focus-time events. For example, searching for "Office" or "Bureau" 
            returns working location events of type officeLocation, whereas searching for "Out of office"
            or "Abwesend" returns out-of-office events. Optional.
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
    attendees: Optional[str] = None,
    all_day: bool = False,
    color_id: Optional[str] = None,
    recurrence: Optional[str] = None,
    reminders: Optional[str] = None,
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
        start: Event start time as an object containing either dateTime+timeZone or date for all-day events.
        end: Event end time as an object containing either dateTime+timeZone or date for all-day event
        max_attendees: Maximum number of attendees (integer).
        send_updates: Guest notification behavior ('all', 'externalOnly', 'none').
        summary: Title of the event.
        timezone: IANA timezone name (e.g., 'Europe/Berlin').
        description: Long text description of the event.
        location: Human-readable location string.
        attendees: list of attendee objects.
            Each object MUST be a dict with at least "email" key.
            Optional keys: displayName, optional (bool), comment, additionalGuests (int).
            INCORRECT: ["alice@example.com", "bob@example.com"]
            CORRECT: [{"email":"alice@example.com"},{"email":"bob@example.com","displayName":"Bob"}]
        all_day: True if this is an all-day event (uses date-only format).
        color_id: Optional color ID (1-11).
        recurrence: List of recurrence rule strings (RRULE, EXRULE, RDATE, EXDATE).
        reminders: Dict with `useDefault` (bool) and `overrides` (list of {method, minutes}).
        transparency: Whether the event blocks calendar time ('opaque' or 'transparent').
        visibility: Visibility settings ('default', 'public', 'private', 'confidential').
        guests_can_invite_others: Boolean indicating whether guests may invite others.
        guests_can_modify: Boolean indicating whether guests may modify the event.
        guests_can_see_other_guests: Boolean indicating whether guests can view other attendees.

    """
    try:
        # Parse JSON strings into proper data structures
        attendees_parsed = json.loads(attendees) if attendees else None
        recurrence_parsed = json.loads(recurrence) if recurrence else None
        reminders_parsed = json.loads(reminders) if reminders else None
        
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
            attendees=attendees_parsed,
            all_day=all_day,
            color_id=color_id,
            recurrence=recurrence_parsed,
            reminders=reminders_parsed,
            transparency=transparency,
            visibility=visibility,
            guests_can_invite_others=guests_can_invite_others,
            guests_can_modify=guests_can_modify,
            guests_can_see_other_guests=guests_can_see_other_guests,
        )
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON in attendees, recurrence, or reminders: {str(e)}", "type": "JSONDecodeError"}
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}



@mcp.tool(
    name="get_calendar_list",
    description=(
        "Lists all Google Calendars of the user. "
        "Supports optional filter parameters such as max_results, min_access_role and show_hidden. "
        "See: https://developers.google.com/calendar/api/v3/reference/calendarList/list"
    ),
)
async def get_calendar_list(
    max_results: Optional[int] = None,
    min_access_role: Optional[str] = None,
    show_hidden: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Lists all calendars of the user.

    Args:
        max_results: Maximum number of calendars to return.
        min_access_role: Minimum access role required ('freeBusyReader', 'reader', 'writer', 'owner').
        show_hidden: Whether to include hidden calendars.
    """
    try:
        client = GoogleCalendarClient()
        return await client.get_calendars(
            max_results=max_results,
            min_access_role=min_access_role,
            show_hidden=show_hidden,
        )
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}


@mcp.tool(
    name="delete_calendar_event",
    description=(
        "Deletes a Google Calendar event by ID. "
        "See: https://developers.google.com/calendar/api/v3/reference/events/delete"
    ),
)
async def delete_calendar_event(
    calendar_id: str,
    event_id: str,
    send_updates: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Deletes an event from the specified Google Calendar.

    Args:
        calendar_id: The ID of the calendar containing the event.
        event_id: The ID of the event to delete.
        send_updates: Guest notification behavior ('all', 'externalOnly', 'none').

    Returns:
        A dict indicating result, e.g., {"status": "deleted"} on success.
    """
    try:
        client = GoogleCalendarClient()
        return await client.delete_event(
            calendar_id=calendar_id,
            event_id=event_id,
            send_updates=send_updates,
        )
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}


if __name__ == "__main__":
    mcp.run()
