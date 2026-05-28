"""
schedule.py — Public tech daily schedule page.

Serves a mobile-first HTML page showing a technician's appointments for today.
No login required — access is controlled by a unique per-tech token.

Endpoints:
  GET /schedule/tech/{token}   — mobile daily schedule page for one technician
"""

from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.technician import Technician
from app.models.appointment import Appointment
from app.models.customer import Customer
from app.models.service_type import ServiceType

router = APIRouter(tags=["schedule"])


def _get_tech_or_404(token: str, db: Session) -> Technician:
    tech = db.query(Technician).filter(Technician.schedule_token == token).first()
    if not tech:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return tech


def _format_time(dt: datetime, tz: ZoneInfo) -> str:
    """Convert UTC datetime to local time string like '9:00 AM'."""
    local = dt.replace(tzinfo=timezone.utc).astimezone(tz)
    return local.strftime("%-I:%M %p")


@router.get("/schedule/tech/{token}", response_class=HTMLResponse)
def tech_daily_schedule(token: str, db: Session = Depends(get_db)):
    """
    Public daily schedule page for a single technician.
    Dynamically queries today's appointments — no nightly cron needed.
    """
    tech = _get_tech_or_404(token, db)

    # Determine the business timezone
    business = tech.business
    tz_str = getattr(business, "timezone", "America/New_York") or "America/New_York"
    try:
        tz = ZoneInfo(tz_str)
    except Exception:
        tz = ZoneInfo("America/New_York")

    brand_color = getattr(business, "brand_color", None) or "#2563eb"
    business_name = business.name

    # Compute start/end of "today" in local timezone
    now_local = datetime.now(tz)
    today_start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end_local = today_start_local + timedelta(days=1)

    # Convert to UTC for DB query
    today_start_utc = today_start_local.astimezone(timezone.utc).replace(tzinfo=None)
    today_end_utc = today_end_local.astimezone(timezone.utc).replace(tzinfo=None)

    appointments = (
        db.query(Appointment)
        .filter(
            Appointment.technician_id == tech.id,
            Appointment.scheduled_start >= today_start_utc,
            Appointment.scheduled_start < today_end_utc,
            Appointment.status.notin_(["cancelled", "no_show"]),
        )
        .order_by(Appointment.scheduled_start)
        .all()
    )

    # Build appointment cards HTML
    today_label = now_local.strftime("%A, %B %-d, %Y")
    appt_count = len(appointments)

    def _card(index: int, appt: Appointment) -> str:
        customer = appt.customer
        service = appt.service_type

        customer_name = customer.full_name if customer else "Unknown Customer"
        customer_phone = customer.phone if customer else None
        service_name = service.name if service else "Service"
        start_time = _format_time(appt.scheduled_start, tz)
        end_time = _format_time(appt.scheduled_end, tz)
        address = appt.address or ""
        problem = appt.problem_description or ""

        # Phone link
        phone_html = ""
        if customer_phone:
            clean_phone = "".join(c for c in customer_phone if c.isdigit() or c == "+")
            phone_html = f'<a href="tel:{clean_phone}" class="phone-link">{customer_phone}</a>'

        # Address link (Google Maps)
        maps_html = ""
        if address:
            import urllib.parse
            maps_url = "https://maps.google.com/?q=" + urllib.parse.quote(address)
            maps_html = f'<a href="{maps_url}" class="address-link" target="_blank" rel="noopener">{address} ↗</a>'

        # Problem description block
        problem_html = ""
        if problem:
            problem_html = f"""
            <div class="problem-block">
              <div class="problem-label">Problem description</div>
              <div class="problem-text">{problem}</div>
            </div>"""

        status_badge = ""
        if appt.status == "confirmed":
            status_badge = '<span class="badge badge-confirmed">Confirmed</span>'
        elif appt.status == "completed":
            status_badge = '<span class="badge badge-completed">Completed</span>'
        elif appt.status == "pending":
            status_badge = '<span class="badge badge-pending">Pending</span>'

        return f"""
      <div class="appt-card">
        <div class="appt-header">
          <div class="appt-number">#{index}</div>
          <div class="appt-time">{start_time} – {end_time}</div>
          {status_badge}
        </div>
        <div class="appt-service">{service_name}</div>
        <div class="appt-customer">{customer_name}</div>
        {"<div class='appt-phone'>" + phone_html + "</div>" if phone_html else ""}
        {"<div class='appt-address'>" + maps_html + "</div>" if maps_html else ""}
        {problem_html}
      </div>"""

    if appt_count == 0:
        body_html = """
      <div class="empty-state">
        <div class="empty-icon">🌴</div>
        <div class="empty-title">No appointments today</div>
        <div class="empty-sub">Enjoy your day off!</div>
      </div>"""
    else:
        cards = "\n".join(_card(i + 1, a) for i, a in enumerate(appointments))
        body_html = f"""
      <div class="summary-bar">{appt_count} appointment{"s" if appt_count != 1 else ""} today</div>
      {cards}"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0" />
  <title>My Schedule – {today_label}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #f3f4f6;
      color: #111827;
      min-height: 100vh;
    }}

    .page-header {{
      background: {brand_color};
      color: #fff;
      padding: 20px 16px 16px;
      position: sticky;
      top: 0;
      z-index: 10;
    }}

    .header-business {{
      font-size: 12px;
      opacity: 0.85;
      font-weight: 500;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      margin-bottom: 4px;
    }}

    .header-tech {{
      font-size: 20px;
      font-weight: 700;
      margin-bottom: 2px;
    }}

    .header-date {{
      font-size: 14px;
      opacity: 0.85;
    }}

    .content {{
      padding: 16px;
      max-width: 600px;
      margin: 0 auto;
    }}

    .summary-bar {{
      font-size: 13px;
      font-weight: 600;
      color: #6b7280;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      margin-bottom: 12px;
      padding: 0 2px;
    }}

    .appt-card {{
      background: #fff;
      border-radius: 12px;
      padding: 16px;
      margin-bottom: 12px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.08);
      border-left: 4px solid {brand_color};
    }}

    .appt-header {{
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 8px;
      flex-wrap: wrap;
    }}

    .appt-number {{
      width: 28px;
      height: 28px;
      border-radius: 50%;
      background: {brand_color};
      color: #fff;
      font-size: 13px;
      font-weight: 700;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }}

    .appt-time {{
      font-size: 16px;
      font-weight: 700;
      color: #111827;
      flex: 1;
    }}

    .badge {{
      font-size: 11px;
      font-weight: 600;
      padding: 2px 8px;
      border-radius: 999px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}

    .badge-confirmed {{ background: #dcfce7; color: #166534; }}
    .badge-completed {{ background: #e0e7ff; color: #3730a3; }}
    .badge-pending {{ background: #fef9c3; color: #854d0e; }}

    .appt-service {{
      font-size: 15px;
      font-weight: 600;
      color: {brand_color};
      margin-bottom: 4px;
    }}

    .appt-customer {{
      font-size: 15px;
      font-weight: 500;
      color: #111827;
      margin-bottom: 4px;
    }}

    .appt-phone, .appt-address {{
      font-size: 14px;
      margin-bottom: 4px;
    }}

    .phone-link, .address-link {{
      color: {brand_color};
      text-decoration: none;
      font-weight: 500;
    }}

    .phone-link:hover, .address-link:hover {{
      text-decoration: underline;
    }}

    .problem-block {{
      margin-top: 10px;
      padding: 10px 12px;
      background: #f9fafb;
      border-radius: 8px;
      border: 1px solid #e5e7eb;
    }}

    .problem-label {{
      font-size: 11px;
      font-weight: 600;
      color: #9ca3af;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 4px;
    }}

    .problem-text {{
      font-size: 14px;
      color: #374151;
      line-height: 1.5;
    }}

    .empty-state {{
      text-align: center;
      padding: 60px 20px;
    }}

    .empty-icon {{
      font-size: 56px;
      margin-bottom: 16px;
    }}

    .empty-title {{
      font-size: 20px;
      font-weight: 700;
      color: #111827;
      margin-bottom: 6px;
    }}

    .empty-sub {{
      font-size: 15px;
      color: #6b7280;
    }}

    .footer {{
      text-align: center;
      padding: 24px 16px;
      font-size: 12px;
      color: #9ca3af;
    }}
  </style>
</head>
<body>

  <div class="page-header">
    <div class="header-business">{business_name}</div>
    <div class="header-tech">{tech.name}</div>
    <div class="header-date">{today_label}</div>
  </div>

  <div class="content">
    {body_html}
  </div>

  <div class="footer">{business_name} · Schedule for {tech.name}</div>

</body>
</html>"""

    return HTMLResponse(content=html, status_code=200)
