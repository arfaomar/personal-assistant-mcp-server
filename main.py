from typing import Optional, Any, Dict, List
import json
from fastmcp import FastMCP
from apis.wttrin.client import WttrInClient
from apis.google_calendar import GoogleCalendarClient
from apis.db_transit import (DbTransitClient, DbTransitClientConfig)
from apis.geocoder import Geocoder
import os
from dotenv import load_dotenv
load_dotenv()
# Initialize the MCP server
mcp = FastMCP("Personal AI Assistant MCP Server")
# Initialize the wttr.in client
wttr = WttrInClient()

# Initialize the DB Transit client
db_transit = DbTransitClient(
    DbTransitClientConfig(
        base_url="https://v6.db.transport.rest"
    )
)


@mcp.tool(
    name="geocode_location",
    description="Converts a place name or address into latitude & longitude using LocationIQ."
)
async def geocode_location(query: str):
    """
    Args:
        query: City, street, or address. Example: 'Frankfurt am Main, Germany'
    """
    try:
        api_key = os.getenv("LOCATIONIQ_KEY")

        if not api_key:
            raise RuntimeError("Missing LOCATIONIQ_KEY environment variable")

        geocoder = Geocoder(api_key)
        lat, lon = geocoder.geocode(query)

        return {
            "query": query,
            "latitude": lat,
            "longitude": lon
        }

    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}



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
        return {
            "error": f"Invalid JSON in attendees, recurrence, or reminders: {str(e)}",
            "type": "JSONDecodeError",
        }
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


@mcp.tool(
    name="update_calendar_event",
    description=(
        "Updates an existing Google Calendar event by ID. "
        "Performs a full update (PUT) - all fields not provided remain as before, but the complete event is overwritten. "
        "See: https://developers.google.com/calendar/api/v3/reference/events/update"
    ),
)
async def update_calendar_event(
    calendar_id: str,
    event_id: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    max_attendees: Optional[int] = None,
    send_updates: Optional[str] = None,
    summary: Optional[str] = None,
    timezone: Optional[str] = None,
    description: Optional[str] = None,
    location: Optional[str] = None,
    attendees: Optional[str] = None,
    all_day: Optional[bool] = None,
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
    Updates an existing event in Google Calendar using PUT (full update).

    The function loads the event, overwrites the specified fields, and saves the complete event object back.
    All fields not specified remain as in the original event.

    Args:
        calendar_id: The ID of the calendar containing the event.
        event_id: The ID of the event to update.
        start: New event start time (RFC3339 dateTime or YYYY-MM-DD for all-day).
        end: New event end time (RFC3339 dateTime or YYYY-MM-DD for all-day).
        max_attendees: Maximum number of attendees (integer).
        send_updates: Guest notification behavior ('all', 'externalOnly', 'none').
        summary: New title of the event.
        timezone: IANA timezone name (e.g., 'Europe/Berlin').
        description: New long text description of the event.
        location: New human-readable location string.
        attendees: New list of attendee objects (JSON string).
            Each object MUST be a dict with at least "email" key.
            Example: [{"email":"alice@example.com"},{"email":"bob@example.com","displayName":"Bob"}]
        all_day: True if this should be changed to an all-day event.
        color_id: New color ID (1-11).
        recurrence: New list of recurrence rule strings (JSON string).
        reminders: New reminder settings (JSON string).
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
        return await client.update_event(
            calendar_id=calendar_id,
            event_id=event_id,
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
        return {
            "error": f"Invalid JSON in attendees, recurrence, or reminders: {str(e)}",
            "type": "JSONDecodeError",
        }
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}

@mcp.tool(
    name="search_points_of_interest",
    description=(
        "Searches for points of interest (POI) matching a free-text query using DB transport.rest API."
        "It also can search for stops, addresses"
    ),
)
async def search_points_of_interest(
    query: str,
    max_results: int = 5,
    language: str = "de",
) -> Dict[str, Any]:
    """
    Searches for points of interest (POI) matching a free-text query.
    Args:
        query: Free-text query, e.g. station name, address, POI.
        max_results: Maximum number of locations to return.
        language: Language for textual fields (e.g. 'de', 'en').
    """
    try:
        return await db_transit.search_locations(
            query=query,
            max_results=max_results,
            language=language,
        )
    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
        }

@mcp.tool(
    name="find_nearest_public_transport_stop",
    description=(
        "Finds the nearest public transport stop to the given place name "
        "(city, street, or full address). "
        "Example: 'Frankfurt', 'München Hbf', 'Berliner Allee 10 Frankfurt'."
    ),
)
async def find_nearest_public_transport_stop(
    query: str,
    max_distance: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Looks up the nearest public transport stop to a place name.

    Args:
        query: City name, street name or address.
        max_distance: Optional walking distance in meters.
    """
    try:

        api_key = os.getenv("LOCATIONIQ_KEY")
        if not api_key:
            raise RuntimeError("Missing LOCATIONIQ_KEY environment variable")

        geocoder = Geocoder(api_key)
        lat, lon = geocoder.geocode(query)

        return await db_transit.find_nearest_stop(
            lon=lon,
            lat=lat,
            max_distance=max_distance,
        )

    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
        }

@mcp.tool(
    name="search_public_transport_journey",
    description=(
        "Searches for public transport journeys between two locations. "
        "Locations can be place names, addresses, or public transport stops/stations."
    ),
)
async def search_public_transport_journeys(
    from_query: str,
    to_query: str,
    departure_time: Optional[str] = None,
    arrival_time: Optional[str] = None,
    max_results: int = 5,
    language: str = "de",
    start_with_walking: bool = True,
) -> Dict[str, Any]:
    """
    Searches for public transport journeys between two locations.
    It queries the DB transport.rest /journeys endpoint for public transport routes.

    Args:
        from_query: City name, street name or address of origin
        to_query: City name, street name or address of destination
        departure_time: Optional ISO 8601 date-time string for desired departure.
        arrival_time: Optional ISO 8601 date-time string for desired arrival.
                          Must not be combined with departure_time.
        max_results: Maximum number of journeys to return (DB default is 3).
        language: Language for textual fields (e.g. 'de' or 'en').
        start_with_walking: Whether to include walking from the origin to
                                the first stop (recommended True).
    """
    try:
        api_key = os.getenv("LOCATIONIQ_KEY")
        if not api_key:
            raise RuntimeError("Missing LOCATIONIQ_KEY environment variable")

        geocoder = Geocoder(api_key)
        from_lat, from_lon = geocoder.geocode(from_query)
        to_lat, to_lon = geocoder.geocode(to_query)

        return await db_transit.journey_search(
            origin_lon=from_lon,
            origin_lat=from_lat,
            dest_lon=to_lon,
            dest_lat=to_lat,
            departure_time=departure_time,
            arrival_time=arrival_time,
            max_results=max_results,
            language=language,
            start_with_walking=start_with_walking,
        )
    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__,
        }


if __name__ == "__main__":
    mcp.run()

