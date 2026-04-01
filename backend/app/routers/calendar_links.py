"""Public calendar link endpoints — no auth required."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse, Response, HTMLResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.appointment import Appointment
from app.utils.ics_generator import (
    generate_ics_file,
    google_calendar_url,
    outlook_calendar_url,
    yahoo_calendar_url,
    get_all_calendar_links,
)

router = APIRouter(prefix="/cal", tags=["calendar"])


def _get_appointment_by_token(token: str, db: Session) -> Appointment:
    appt = db.query(Appointment).filter(Appointment.calendar_token == token).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appt


def _build_event_details(appt: Appointment) -> dict:
    service_name = appt.service_type.name if appt.service_type else "Service Appointment"
    tech_name = appt.technician.name if appt.technician else "TBD"
    customer_name = appt.customer.full_name if appt.customer else ""
    location = appt.address or (appt.customer.address if appt.customer else "")

    title = f"{service_name} - Home Services"
    description = (
        f"Service: {service_name}\\n"
        f"Technician: {tech_name}\\n"
        f"Customer: {customer_name}\\n"
        f"Address: {location}"
    )
    return {
        "title": title,
        "start": appt.scheduled_start,
        "end": appt.scheduled_end,
        "description": description,
        "location": location or "",
    }


@router.get("/{token}")
def calendar_landing_page(token: str, db: Session = Depends(get_db)):
    """Render a simple landing page with all 'Add to Calendar' options."""
    appt = _get_appointment_by_token(token, db)
    details = _build_event_details(appt)
    links = get_all_calendar_links(token)

    service_name = appt.service_type.name if appt.service_type else "Appointment"
    tech_name = appt.technician.name if appt.technician else "TBD"
    date_str = appt.scheduled_start.strftime("%A, %B %d, %Y")
    time_str = f"{appt.scheduled_start.strftime('%I:%M %p')} - {appt.scheduled_end.strftime('%I:%M %p')}"
    location = appt.address or (appt.customer.address if appt.customer else "N/A")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Add to Calendar - {service_name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
               background: #f5f5f5; color: #333; padding: 20px; }}
        .card {{ max-width: 480px; margin: 40px auto; background: white; border-radius: 12px;
                 box-shadow: 0 2px 12px rgba(0,0,0,0.1); overflow: hidden; }}
        .header {{ background: #2563eb; color: white; padding: 24px; text-align: center; }}
        .header h1 {{ font-size: 20px; margin-bottom: 4px; }}
        .header p {{ opacity: 0.9; font-size: 14px; }}
        .details {{ padding: 24px; }}
        .detail-row {{ display: flex; margin-bottom: 16px; }}
        .detail-label {{ font-weight: 600; width: 100px; flex-shrink: 0; color: #666; }}
        .detail-value {{ color: #333; }}
        .buttons {{ padding: 0 24px 24px; display: flex; flex-direction: column; gap: 10px; }}
        .btn {{ display: block; text-align: center; padding: 14px; border-radius: 8px;
                text-decoration: none; font-weight: 600; font-size: 15px; }}
        .btn-google {{ background: #4285f4; color: white; }}
        .btn-apple {{ background: #333; color: white; }}
        .btn-outlook {{ background: #0078d4; color: white; }}
        .btn-yahoo {{ background: #6001d2; color: white; }}
        .btn:hover {{ opacity: 0.9; }}
    </style>
</head>
<body>
    <div class="card">
        <div class="header">
            <h1>{service_name}</h1>
            <p>Your appointment details</p>
        </div>
        <div class="details">
            <div class="detail-row">
                <span class="detail-label">Date</span>
                <span class="detail-value">{date_str}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Time</span>
                <span class="detail-value">{time_str}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Technician</span>
                <span class="detail-value">{tech_name}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Location</span>
                <span class="detail-value">{location}</span>
            </div>
        </div>
        <div class="buttons">
            <a href="{links['google']}" target="_blank" class="btn btn-google">Add to Google Calendar</a>
            <a href="{links['ical']}" class="btn btn-apple">Add to Apple Calendar</a>
            <a href="{links['outlook']}" target="_blank" class="btn btn-outlook">Add to Outlook</a>
            <a href="{links['yahoo']}" target="_blank" class="btn btn-yahoo">Add to Yahoo Calendar</a>
        </div>
    </div>
</body>
</html>"""
    return HTMLResponse(content=html)


@router.get("/{token}/google")
def add_to_google(token: str, db: Session = Depends(get_db)):
    appt = _get_appointment_by_token(token, db)
    details = _build_event_details(appt)
    url = google_calendar_url(**details)
    return RedirectResponse(url=url)


@router.get("/{token}/ical")
def download_ical(token: str, db: Session = Depends(get_db)):
    appt = _get_appointment_by_token(token, db)
    details = _build_event_details(appt)
    ics_content = generate_ics_file(
        appointment_id=appt.id,
        title=details["title"],
        start=details["start"],
        end=details["end"],
        description=details["description"],
        location=details["location"],
    )
    return Response(
        content=ics_content,
        media_type="text/calendar",
        headers={"Content-Disposition": f"attachment; filename=appointment-{appt.id}.ics"},
    )


@router.get("/{token}/outlook")
def add_to_outlook(token: str, db: Session = Depends(get_db)):
    appt = _get_appointment_by_token(token, db)
    details = _build_event_details(appt)
    url = outlook_calendar_url(**details)
    return RedirectResponse(url=url)


@router.get("/{token}/yahoo")
def add_to_yahoo(token: str, db: Session = Depends(get_db)):
    appt = _get_appointment_by_token(token, db)
    details = _build_event_details(appt)
    url = yahoo_calendar_url(**details)
    return RedirectResponse(url=url)
