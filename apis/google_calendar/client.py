from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import os
from pathlib import Path
import httpx
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


SCOPES = [
    "https://www.googleapis.com/auth/calendar",
]


class GoogleCalendarClient:
    """Async wrapper for Google Calendar API v3 using httpx."""

    BASE_URL = "https://www.googleapis.com/calendar/v3"


    def __init__(self) -> None:
        # Always load .env from the project root (one level above 'apis')
        dotenv_path = Path(__file__).resolve().parents[2] / ".env"
        load_dotenv(dotenv_path)

        # Read paths from env variables
        self.credentials_file = os.environ.get("GOOGLE_CALENDAR_CREDENTIALS_FILE")
        if not self.credentials_file:
            raise KeyError(
                "Environment variable 'GOOGLE_CALENDAR_CREDENTIALS_FILE' not set. "
                "Make sure your .env contains: GOOGLE_CALENDAR_CREDENTIALS_FILE=C:/full/path/to/credentials.json"
            )
        
        self.token_file = os.environ.get("GOOGLE_CALENDAR_TOKEN_FILE")
        if not self.token_file:
            raise KeyError(
                "Environment variable 'GOOGLE_CALENDAR_TOKEN_FILE' not set. "
                "Make sure your .env contains: GOOGLE_CALENDAR_TOKEN_FILE=C:/full/path/to/token.json"
            )

        self.loaded_credentials: Optional[Credentials] = None

    def _load_credentials(self) -> Credentials:
        """Load or obtain OAuth credentials."""
        if self.loaded_credentials and self.loaded_credentials.valid:
            return self.loaded_credentials

        creds: Optional[Credentials] = None
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"OAuth client secrets not found at: {self.credentials_file}. "
                        "Please check the path in your .env file."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES
                )
                creds = flow.run_local_server(port=0)

            with open(self.token_file, "w", encoding="utf-8") as token:
                token.write(creds.to_json())

        self.loaded_credentials = creds
        return creds

    def _get_auth_headers(self) -> Dict[str, str]:
        """Return authorization headers with current access token."""
        creds = self._load_credentials()
        return {"Authorization": f"Bearer {creds.token}"}

    async def list_events(
        self,
        calendar_id: str = "primary",
        time_min: Optional[str] = None,
        time_max: Optional[str] = None,
        max_results: Optional[int] = None,
        q: Optional[str] = None,
        single_events: bool = True,
        order_by: Optional[str] = "startTime",
    ) -> Dict[str, Any]:
        """List events using Calendar API Events.list.

        All optional parameters map
        directly to the Calendar API fields documented at:
        https://developers.google.com/calendar/api/v3/reference/events/list
        """
        now = datetime.now(timezone.utc)
        if time_min is None:
            time_min = now.isoformat()
        if time_max is None:
            time_max = (
                now + timedelta(days=7)
            ).isoformat()  # Unspecified time bounds default to the next 7 days to avoid returning a very large result set by accident

        params: Dict[str, Any] = {
            "timeMin": time_min,
            "timeMax": time_max,
            "singleEvents": single_events,
            "orderBy": order_by,
        }
        if max_results is not None:
            params["maxResults"] = max_results
        if q:
            params["q"] = q

        url = f"{self.BASE_URL}/calendars/{calendar_id}/events"
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                url, params=params, headers=self._get_auth_headers()
            )
            resp.raise_for_status()
            return resp.json()

    async def create_event(
        self,
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
        """Create an event on a calendar.

        Query parameters map to Events.insert API:
        https://developers.google.com/calendar/api/v3/reference/events/insert
        """
        # Prepare the event body based on whether it is an all-day event or not
        if all_day:
            # Extract the date part (YYYY-MM-DD) for all-day events
            start_date = start.split("T")[0]
            end_date = end.split("T")[0]
            body = {
                "summary": summary,
                "start": {"date": start_date, "timeZone": timezone},
                "end": {"date": end_date, "timeZone": timezone},
            }
        else:
            body = {
                "summary": summary,
                "start": {"dateTime": start, "timeZone": timezone},
                "end": {"dateTime": end, "timeZone": timezone},
            }

        # Optional body fields
        if description:
            body["description"] = description
        if location:
            body["location"] = location
        if attendees:
            body["attendees"] = [{"email": e} for e in attendees]
        if color_id:
            body["colorId"] = color_id
        if recurrence:
            body["recurrence"] = recurrence
        if reminders:
            body["reminders"] = reminders
        if transparency:
            body["transparency"] = transparency
        if visibility:
            body["visibility"] = visibility
        if guests_can_invite_others is not None:
            body["guestsCanInviteOthers"] = guests_can_invite_others
        if guests_can_modify is not None:
            body["guestsCanModify"] = guests_can_modify
        if guests_can_see_other_guests is not None:
            body["guestsCanSeeOtherGuests"] = guests_can_see_other_guests

        # optional Query parameters
        params: Dict[str, Any] = {}
        if max_attendees is not None:
            params["maxAttendees"] = max_attendees
        if send_updates:
            params["sendUpdates"] = send_updates

        url = f"{self.BASE_URL}/calendars/{calendar_id}/events"
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url, json=body, params=params, headers=self._get_auth_headers()
            )
            resp.raise_for_status()
            return resp.json()

    async def get_calendars(
        self,
        max_results: Optional[int] = None,
        min_access_role: Optional[str] = None,
        show_hidden: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Return the list of calendars available to the user.
        Optional query parameters map to:
        https://developers.google.com/calendar/api/v3/reference/calendarList/list
        """
        url = f"{self.BASE_URL}/users/me/calendarList"
        params: Dict[str, Any] = {}
        if max_results is not None:
            params["maxResults"] = max_results
        if min_access_role is not None:
            params["minAccessRole"] = min_access_role
        if show_hidden is not None:
            params["showHidden"] = str(show_hidden).lower()

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                url, params=params, headers=self._get_auth_headers()
            )
            resp.raise_for_status()
            return resp.json()

    async def delete_event(
        self,
        calendar_id: str,
        event_id: str,
        send_updates: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Delete an event from a calendar.

        Maps to Events.delete:
        https://developers.google.com/calendar/api/v3/reference/events/delete

        Args:
            calendar_id: The ID of the calendar.
            event_id: The ID of the event to delete.
            send_updates: Guest notification behavior ('all', 'externalOnly', 'none').

        Returns:
            A dict indicating success. Google API returns 204 No Content on success;
            we normalize to {"status": "deleted"}.
        """
        url = f"{self.BASE_URL}/calendars/{calendar_id}/events/{event_id}"
        params: Dict[str, Any] = {}
        if send_updates:
            params["sendUpdates"] = send_updates

        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                url, params=params, headers=self._get_auth_headers()
            )
            resp.raise_for_status()
            return {"status": "deleted"}

    async def update_event(
        self,
        calendar_id: str,
        event_id: str,
        # all other fields optional, as before
        max_attendees: Optional[int] = None,
        send_updates: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        summary: Optional[str] = None,
        timezone: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[Dict[str, Any]]] = None,
        all_day: Optional[bool] = None,
        color_id: Optional[str] = None,
        recurrence: Optional[List[str]] = None,
        reminders: Optional[Dict[str, Any]] = None,
        transparency: Optional[str] = None,
        visibility: Optional[str] = None,
        guests_can_invite_others: Optional[bool] = None,
        guests_can_modify: Optional[bool] = None,
        guests_can_see_other_guests: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Update an existing event on a calendar using PUT (full update).
        Loads the event via GET, overwrites specified fields, sends the complete event via PUT.
        https://developers.google.com/calendar/api/v3/reference/events/update
        """
        url = f"{self.BASE_URL}/calendars/{calendar_id}/events/{event_id}"
        params: Dict[str, Any] = {}
        if max_attendees is not None:
            params["maxAttendees"] = max_attendees
        if send_updates:
            params["sendUpdates"] = send_updates

        async with httpx.AsyncClient() as client:
            # 1. Load the event via GET
            get_resp = await client.get(url, headers=self._get_auth_headers())
            get_resp.raise_for_status()
            event = get_resp.json()

            # 2. Overwrite fields if specified
            if start is not None and end is not None:
                if all_day:
                    start_date = start.split("T")[0]
                    end_date = end.split("T")[0]
                    event["start"] = {"date": start_date, "timeZone": timezone}
                    event["end"] = {"date": end_date, "timeZone": timezone}
                else:
                    event["start"] = {"dateTime": start, "timeZone": timezone}
                    event["end"] = {"dateTime": end, "timeZone": timezone}
            if summary is not None:
                event["summary"] = summary
            if description is not None:
                event["description"] = description
            if location is not None:
                event["location"] = location
            if attendees is not None:
                event["attendees"] = attendees
            if color_id is not None:
                event["colorId"] = color_id
            if recurrence is not None:
                event["recurrence"] = recurrence
            if reminders is not None:
                event["reminders"] = reminders
            if transparency is not None:
                event["transparency"] = transparency
            if visibility is not None:
                event["visibility"] = visibility
            if guests_can_invite_others is not None:
                event["guestsCanInviteOthers"] = guests_can_invite_others
            if guests_can_modify is not None:
                event["guestsCanModify"] = guests_can_modify
            if guests_can_see_other_guests is not None:
                event["guestsCanSeeOtherGuests"] = guests_can_see_other_guests

            # 3. Send the complete event via PUT
            put_resp = await client.put(
                url, json=event, params=params, headers=self._get_auth_headers()
            )
            put_resp.raise_for_status()
            return put_resp.json()
