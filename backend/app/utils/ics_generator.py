"""iCalendar (.ics) file and calendar URL generation."""

from datetime import datetime
from urllib.parse import quote

from app.config import settings


def format_ics_datetime(dt: datetime) -> str:
    """Format datetime for iCalendar: 20260401T140000Z"""
    return dt.strftime("%Y%m%dT%H%M%SZ")


def generate_ics_file(
    appointment_id: int,
    title: str,
    start: datetime,
    end: datetime,
    description: str,
    location: str,
) -> str:
    """Generate a valid .ics file string."""
    return (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//HomeServices//Appointment//EN\r\n"
        "CALSCALE:GREGORIAN\r\n"
        "METHOD:PUBLISH\r\n"
        "BEGIN:VEVENT\r\n"
        f"UID:appointment-{appointment_id}@homeservices\r\n"
        f"DTSTART:{format_ics_datetime(start)}\r\n"
        f"DTEND:{format_ics_datetime(end)}\r\n"
        f"SUMMARY:{title}\r\n"
        f"DESCRIPTION:{description}\r\n"
        f"LOCATION:{location}\r\n"
        "STATUS:CONFIRMED\r\n"
        "BEGIN:VALARM\r\n"
        "TRIGGER:-PT1H\r\n"
        "DESCRIPTION:Appointment reminder\r\n"
        "ACTION:DISPLAY\r\n"
        "END:VALARM\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )


def google_calendar_url(title: str, start: datetime, end: datetime, description: str, location: str) -> str:
    """Build a Google Calendar 'add event' URL."""
    base = "https://calendar.google.com/calendar/render"
    dates = f"{format_ics_datetime(start)}/{format_ics_datetime(end)}"
    return (
        f"{base}?action=TEMPLATE"
        f"&text={quote(title)}"
        f"&dates={dates}"
        f"&details={quote(description)}"
        f"&location={quote(location)}"
    )


def outlook_calendar_url(title: str, start: datetime, end: datetime, description: str, location: str) -> str:
    """Build an Outlook.com 'add event' URL."""
    base = "https://outlook.live.com/calendar/0/action/compose"
    return (
        f"{base}?rru=addevent"
        f"&subject={quote(title)}"
        f"&startdt={start.isoformat()}Z"
        f"&enddt={end.isoformat()}Z"
        f"&body={quote(description)}"
        f"&location={quote(location)}"
    )


def yahoo_calendar_url(title: str, start: datetime, end: datetime, description: str, location: str) -> str:
    """Build a Yahoo Calendar 'add event' URL."""
    base = "https://calendar.yahoo.com/"
    dur_minutes = int((end - start).total_seconds() / 60)
    dur_hours = dur_minutes // 60
    dur_rem = dur_minutes % 60
    duration = f"{dur_hours:02d}{dur_rem:02d}"
    return (
        f"{base}?v=60"
        f"&title={quote(title)}"
        f"&st={format_ics_datetime(start)}"
        f"&dur={duration}"
        f"&desc={quote(description)}"
        f"&in_loc={quote(location)}"
    )


def get_all_calendar_links(token: str) -> dict:
    """Return all calendar link URLs for a given appointment token."""
    base = settings.BASE_URL
    return {
        "landing_page": f"{base}/cal/{token}",
        "google": f"{base}/cal/{token}/google",
        "ical": f"{base}/cal/{token}/ical",
        "outlook": f"{base}/cal/{token}/outlook",
        "yahoo": f"{base}/cal/{token}/yahoo",
    }
