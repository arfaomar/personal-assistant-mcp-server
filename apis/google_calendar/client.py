from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import os

import httpx
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


SCOPES = [
    "https://www.googleapis.com/auth/calendar",
]

class GoogleCalendarClient:
    """Async wrapper for Google Calendar API v3 using httpx."""
    
    BASE_URL = "https://www.googleapis.com/calendar/v3"
    
    def __init__(
        self,
        credentials_file: Optional[str] = None,
        token_file: Optional[str] = None,
    ) -> None:
        self.credentials_file = (
            credentials_file
            or os.environ.get("GOOGLE_CALENDAR_CREDENTIALS_FILE")
            or os.path.join(os.getcwd(), "credentials.json")
        )
        self.token_file = (
            token_file
            or os.environ.get("GOOGLE_CALENDAR_TOKEN_FILE")
            or os.path.join(os.getcwd(), "token.json")
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
                        "Create a Google Cloud OAuth 2.0 Client ID (Desktop) and download credentials.json."
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
            time_max = (now + timedelta(days=7)).isoformat() #Unspecified time bounds default to the next 7 days to avoid returning a very large result set by accident

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
            resp = await client.get(url, params=params, headers=self._get_auth_headers())
            resp.raise_for_status()
            return resp.json()

    async def create_event(
        self,
        # required parameters
        calendar_id: str,
        start: str,  # RFC3339 dateTime string or YYYY-MM-DD for all-day events
        end: str,  # RFC3339 dateTime string or YYYY-MM-DD for all-day events
        
        # optional query parameters 
        max_attendees: Optional[int] = None,
        send_updates: Optional[str] = None,
        
        # optional body parameters
        summary: str = "untitled event",  # Event title displayed in the calendar UI
        timezone: Optional[str] = None,  # IANA timezone name (e.g., "Europe/Berlin")
        description: Optional[str] = None,  # Optional long text description
        location: Optional[str] = None,  # Optional human-readable location
        # attendees:
        # each dict can contain:
        #   - "email" (required per attendee)
        #   - "displayName" (optional)
        #   - "optional" (bool)
        #   - "comment" (str)
        #   - "additionalGuests" (int)
        attendees: Optional[List[Dict[str, Any]]] = None,       
        all_day: bool = False,  # If True, encode start/end as date-only in the API body
        color_id: Optional[str] = None,  # Optional color ID (1-11)
        recurrence: Optional[List[str]] = None,  # Optional list of RRULE/EXRULE/RDATE/EXDATE strings
        reminders: Optional[Dict[str, Any]] = None,  # Optional dict with 'useDefault' or 'overrides' list
        transparency: Optional[str] = None,  # 'opaque' (default) or 'transparent'
        visibility: Optional[str] = None,  # 'default', 'public', 'private', or 'confidential'
        guests_can_invite_others: Optional[bool] = None,  # Whether guests can invite others (default: True)
        guests_can_modify: Optional[bool] = None,  # Whether guests can modify the event (default: False)
        guests_can_see_other_guests: Optional[bool] = None,  # Whether guests see other guests (default: True)

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
            resp = await client.post(url, json=body, params=params, headers=self._get_auth_headers())
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
            resp = await client.get(url, params=params, headers=self._get_auth_headers())
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
            resp = await client.delete(url, params=params, headers=self._get_auth_headers())
            resp.raise_for_status()
            return {"status": "deleted"}
