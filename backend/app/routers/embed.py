"""
embed.py — Public embeddable contact form served as a standalone HTML page.

Clients paste a single <iframe> tag into their website.
The iframe loads a fully self-contained form page styled with the business's
brand color and pre-populated with their service list.

Endpoints:
  GET  /embed/{slug}/contact          — serves the iframe HTML page
  GET  /embed/{slug}/contact-config   — returns JSON config for the form
"""

import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.business import Business
from app.models.service_type import ServiceType

logger = logging.getLogger(__name__)
router = APIRouter(tags=["embed"])


def _get_business_or_404(slug: str, db: Session) -> Business:
    business = db.query(Business).filter(
        Business.slug == slug, Business.is_active == True
    ).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    return business


@router.get("/embed/{slug}/contact-config")
def get_contact_config(slug: str, db: Session = Depends(get_db)):
    """Returns JSON config the embed form uses to render itself."""
    business = _get_business_or_404(slug, db)
    services = db.query(ServiceType).filter(
        ServiceType.business_id == business.id,
        ServiceType.is_active == True,
    ).order_by(ServiceType.name).all()

    return {
        "business_id":   business.id,
        "business_name": business.name,
        "brand_color":   business.brand_color or "#2563eb",
        "phone":         business.phone or "",
        "services":      [s.name for s in services],
    }


@router.get("/embed/{slug}/contact", response_class=HTMLResponse)
def contact_embed(slug: str, db: Session = Depends(get_db)):
    """
    Serves a self-contained HTML contact form page suitable for embedding
    in an <iframe> on any website.
    """
    business = _get_business_or_404(slug, db)
    services = db.query(ServiceType).filter(
        ServiceType.business_id == business.id,
        ServiceType.is_active == True,
    ).order_by(ServiceType.name).all()

    service_names = [s.name for s in services]
    brand_color   = business.brand_color or "#2563eb"
    business_name = business.name
    business_id   = business.id

    # Build the service options HTML
    service_options = "\n".join(
        f'<option value="{name}">{name}</option>'
        for name in service_names
    )

    # Determine submit URL (same origin as this endpoint)
    api_base = "https://api.spacecoaststudios.com"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Contact {business_name}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      font-size: 14px;
      color: #111827;
      background: transparent;
      padding: 16px;
    }}

    .form-title {{
      font-size: 18px;
      font-weight: 700;
      color: {brand_color};
      margin-bottom: 16px;
    }}

    .form-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }}

    .form-group {{
      display: flex;
      flex-direction: column;
      gap: 4px;
    }}

    .form-group.full {{
      grid-column: 1 / -1;
    }}

    label {{
      font-size: 13px;
      font-weight: 500;
      color: #374151;
    }}

    label .required {{
      color: #ef4444;
      margin-left: 2px;
    }}

    input, select, textarea {{
      width: 100%;
      padding: 8px 12px;
      border: 1px solid #d1d5db;
      border-radius: 6px;
      font-size: 14px;
      color: #111827;
      background: #fff;
      transition: border-color 0.15s, box-shadow 0.15s;
      outline: none;
    }}

    input:focus, select:focus, textarea:focus {{
      border-color: {brand_color};
      box-shadow: 0 0 0 3px {brand_color}22;
    }}

    textarea {{
      resize: vertical;
      min-height: 80px;
    }}

    .char-counter {{
      font-size: 11px;
      color: #9ca3af;
      text-align: right;
      margin-top: 2px;
    }}

    .char-counter.near-limit {{
      color: #f59e0b;
    }}

    .char-counter.at-limit {{
      color: #ef4444;
    }}

    .contact-method-group {{
      display: flex;
      gap: 16px;
      flex-wrap: wrap;
    }}

    .contact-method-group label {{
      display: flex;
      align-items: center;
      gap: 6px;
      font-weight: 400;
      cursor: pointer;
    }}

    .contact-method-group input[type="radio"] {{
      width: auto;
      accent-color: {brand_color};
    }}

    .submit-btn {{
      width: 100%;
      padding: 10px;
      background: {brand_color};
      color: #fff;
      border: none;
      border-radius: 6px;
      font-size: 15px;
      font-weight: 600;
      cursor: pointer;
      transition: opacity 0.15s;
      margin-top: 4px;
    }}

    .submit-btn:hover {{ opacity: 0.9; }}
    .submit-btn:disabled {{ opacity: 0.6; cursor: not-allowed; }}

    .alert {{
      padding: 12px 16px;
      border-radius: 6px;
      font-size: 14px;
      margin-bottom: 12px;
      display: none;
    }}

    .alert.success {{
      background: #f0fdf4;
      border: 1px solid #bbf7d0;
      color: #166534;
    }}

    .alert.error {{
      background: #fef2f2;
      border: 1px solid #fecaca;
      color: #991b1b;
    }}

    .success-state {{
      text-align: center;
      padding: 32px 16px;
      display: none;
    }}

    .success-state .check {{
      font-size: 48px;
      margin-bottom: 12px;
    }}

    .success-state h3 {{
      font-size: 18px;
      font-weight: 700;
      color: {brand_color};
      margin-bottom: 8px;
    }}

    .success-state p {{
      color: #6b7280;
      font-size: 14px;
    }}

    .sms-consent-group {{
      margin-top: 4px;
    }}

    .sms-consent-label {{
      display: flex;
      align-items: flex-start;
      gap: 10px;
      cursor: pointer;
      font-size: 12px;
      color: #4b5563;
      line-height: 1.6;
      font-weight: 400;
    }}

    .sms-consent-label input[type="checkbox"] {{
      width: 16px;
      min-width: 16px;
      height: 16px;
      margin-top: 2px;
      accent-color: {brand_color};
      cursor: pointer;
    }}

    .sms-consent-label a {{
      color: {brand_color};
      text-decoration: underline;
    }}

    @media (max-width: 480px) {{
      .form-grid {{ grid-template-columns: 1fr; }}
      .form-group.full {{ grid-column: 1; }}
    }}
  </style>
</head>
<body>

  <div id="successState" class="success-state">
    <div class="check">✅</div>
    <h3>Message Received!</h3>
    <p>Thanks for reaching out. We'll be in touch shortly.</p>
  </div>

  <form id="contactForm">
    <div class="form-title">Contact {business_name}</div>

    <div id="errorAlert" class="alert error"></div>

    <div class="form-grid">

      <div class="form-group">
        <label for="name">Full name <span class="required">*</span></label>
        <input type="text" id="name" name="name" required placeholder="Jane Smith" />
      </div>

      <div class="form-group">
        <label for="phone">Phone number <span class="required">*</span></label>
        <input type="tel" id="phone" name="phone" required placeholder="(321) 555-0100" />
      </div>

      <div class="form-group">
        <label for="email">Email address <span class="required">*</span></label>
        <input type="email" id="email" name="email" required placeholder="jane@example.com" />
      </div>

      <div class="form-group">
        <label for="service">Service needed</label>
        <select id="service" name="service">
          <option value="">— Select a service —</option>
          {service_options}
        </select>
      </div>

      <div class="form-group full">
        <label for="streetAddress">Service Address <span class="required">*</span></label>
        <input type="text" id="streetAddress" name="street_address" required placeholder="123 Main St" />
      </div>

      <div class="form-group">
        <label for="city">City <span class="required">*</span></label>
        <input type="text" id="city" name="city" required placeholder="Cocoa" />
      </div>

      <div class="form-group">
        <label for="state">State</label>
        <input type="text" id="state" name="state" placeholder="FL" maxlength="2" style="text-transform:uppercase;" />
      </div>

      <div class="form-group">
        <label for="zipCode">Zip Code</label>
        <input type="text" id="zipCode" name="zip_code" placeholder="32922" maxlength="10" />
      </div>

      <div class="form-group full">
        <label for="message">Message <span class="required">*</span></label>
        <textarea id="message" name="message" required placeholder="Tell us about your project or issue…"></textarea>
      </div>

      <div class="form-group full">
        <label for="problemDescription">Describe the problem <span style="font-size:12px;color:#6b7280;font-weight:400;">(optional)</span></label>
        <textarea id="problemDescription" name="problem_description" maxlength="200" placeholder="What's going on? Any details help our technician come prepared…" style="min-height:70px;"></textarea>
        <div class="char-counter" id="problemCounter">0 / 200</div>
      </div>

      <div class="form-group full">
        <label>Preferred contact method</label>
        <div class="contact-method-group">
          <label><input type="radio" name="contact_method" value="call" checked /> Phone call</label>
          <label><input type="radio" name="contact_method" value="text" /> Text message</label>
          <label><input type="radio" name="contact_method" value="email" /> Email</label>
        </div>
        <div id="textConsentHint" style="display:none;margin-top:6px;font-size:12px;color:#6b7280;">
          To receive your reply by text, check the SMS consent box below. Without consent, we'll send your response by email instead.
        </div>
      </div>

      <div class="form-group full">
        <div class="sms-consent-group">
          <label class="sms-consent-label">
            <input type="checkbox" id="smsConsent" name="sms_consent" />
            <span>
              (Optional) I agree to receive SMS messages from {business_name},
              including appointment confirmations, reminders, and service-related notifications.
              Msg &amp; data rates may apply. Reply STOP to opt out at any time. Reply HELP for help.
              SMS consent is not required to submit this form or receive service.
              View our <a href="https://spacecoaststudios.com/terms" target="_blank" rel="noopener">Terms</a>
              and <a href="https://spacecoaststudios.com/privacy" target="_blank" rel="noopener">Privacy Policy</a>.
            </span>
          </label>
        </div>
      </div>

      <div class="form-group full">
        <button type="submit" class="submit-btn" id="submitBtn">Send Message</button>
      </div>

    </div>
  </form>

  <script>
    const BUSINESS_ID = {business_id};
    const API_BASE    = "{api_base}";

    // Reset form if browser restores this page from bfcache (back/forward navigation)
    window.addEventListener('pageshow', function(event) {{
      if (event.persisted) {{
        document.getElementById('contactForm').style.display = '';
        document.getElementById('successState').style.display = 'none';
        document.getElementById('contactForm').reset();
      }}
    }});

    // Show/hide the "check consent to receive texts" hint when text method is selected
    (function() {{
      const radios = document.querySelectorAll('input[name="contact_method"]');
      const hint   = document.getElementById("textConsentHint");
      const consentBox = document.getElementById("smsConsent");

      function updateHint() {{
        const isText = document.querySelector('input[name="contact_method"]:checked')?.value === "text";
        hint.style.display = (isText && !consentBox.checked) ? "block" : "none";
      }}

      radios.forEach(r => r.addEventListener("change", updateHint));
      consentBox.addEventListener("change", updateHint);
    }})();

    // Character counter for problem description
    (function() {{
      const textarea = document.getElementById("problemDescription");
      const counter  = document.getElementById("problemCounter");
      const MAX = 200;
      textarea.addEventListener("input", function() {{
        const len = textarea.value.length;
        counter.textContent = len + " / " + MAX;
        counter.className = "char-counter" + (len >= MAX ? " at-limit" : len >= 170 ? " near-limit" : "");
      }});
    }})();

    document.getElementById("contactForm").addEventListener("submit", async function(e) {{
      e.preventDefault();

      const btn       = document.getElementById("submitBtn");
      const errorAlert = document.getElementById("errorAlert");

      btn.disabled    = true;
      btn.textContent = "Sending…";
      errorAlert.style.display = "none";

      const contactMethod = document.querySelector('input[name="contact_method"]:checked')?.value || null;
      // Capture consent state — optional per approved A2P campaign.
      // SMS is only sent server-side when this is true.
      const smsConsent = document.getElementById("smsConsent").checked;

      const problemText = document.getElementById("problemDescription").value.trim();

      const payload = {{
        name:                     document.getElementById("name").value.trim(),
        email:                    document.getElementById("email").value.trim(),
        phone:                    document.getElementById("phone").value.trim(),
        service_requested:        document.getElementById("service").value || null,
        preferred_contact_method: contactMethod,
        sms_consent:              smsConsent,
        message:                  document.getElementById("message").value.trim(),
        problem_description:      problemText || null,
        street_address:           document.getElementById("streetAddress").value.trim() || null,
        city:                     document.getElementById("city").value.trim() || null,
        state:                    document.getElementById("state").value.trim().toUpperCase() || null,
        zip_code:                 document.getElementById("zipCode").value.trim() || null,
      }};

      try {{
        const res = await fetch(`${{API_BASE}}/contact/submit?business_id=${{BUSINESS_ID}}`, {{
          method:  "POST",
          headers: {{ "Content-Type": "application/json" }},
          body:    JSON.stringify(payload),
        }});

        if (!res.ok) {{
          const data = await res.json().catch(() => ({{}}));
          throw new Error(data.detail || "Something went wrong. Please try again.");
        }}

        // Show success state
        document.getElementById("contactForm").style.display = "none";
        document.getElementById("successState").style.display = "block";

        // Notify parent window (useful for resizing the iframe)
        window.parent.postMessage({{ type: "scs_form_submitted" }}, "*");

      }} catch (err) {{
        errorAlert.textContent = err.message;
        errorAlert.style.display = "block";
        btn.disabled    = false;
        btn.textContent = "Send Message";
      }}
    }});
  </script>

</body>
</html>"""

    return HTMLResponse(
        content=html,
        status_code=200,
        headers={"Cache-Control": "no-store"},
    )


# ---------------------------------------------------------------------------
# Self-scheduling booking widget — public, slug-scoped endpoints (Phase 1)
# Reuses the internal availability engine + appointment/notification logic.
# ---------------------------------------------------------------------------

from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
import pytz as _pytz

from app.services.scheduling import (
    get_available_slots, auto_assign_technician,
    get_min_lead_time_hours, get_max_advance_days,
)


def _biz_tz(business):
    try:
        return _pytz.timezone(getattr(business, "timezone", None) or "America/New_York")
    except Exception:
        return _pytz.timezone("America/New_York")


def _to_utc(dt):
    return (dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt).astimezone(timezone.utc)


@router.get("/embed/{slug}/booking-config")
def booking_config(slug: str, db: Session = Depends(get_db)):
    """Public config the booking widget uses to render itself."""
    business = _get_business_or_404(slug, db)
    services = db.query(ServiceType).filter(
        ServiceType.business_id == business.id,
        ServiceType.is_active == True,
        ServiceType.category != "Emergency",   # internal dispatch type — not self-bookable
    ).order_by(ServiceType.name).all()
    return {
        "business_id": business.id,
        "business_name": business.name,
        "brand_color": business.brand_color or "#2563eb",
        "phone": business.phone or "",
        "timezone": getattr(business, "timezone", None) or "America/New_York",
        "min_lead_time_hours": get_min_lead_time_hours(db, business.id),
        "max_advance_booking_days": get_max_advance_days(db, business.id),
        "services": [
            {
                "id": s.id,
                "name": s.name,
                "duration_minutes": s.duration_minutes,
                "price": float(s.base_price) if s.base_price is not None else None,
            }
            for s in services
        ],
    }


@router.get("/embed/{slug}/availability")
def booking_availability(slug: str, service_id: int, days: int = 14, db: Session = Depends(get_db)):
    """Public availability for a service, grouped by local day with display labels."""
    business = _get_business_or_404(slug, db)
    tz = _biz_tz(business)
    max_adv = get_max_advance_days(db, business.id)
    days = max(1, min(days, max_adv))
    today_local = datetime.now(tz).date()
    end_local = today_local + timedelta(days=days)
    raw = get_available_slots(db, business.id, service_id, today_local, end_local)
    out = []
    for day in raw:
        slots = []
        for s in day["slots"]:
            local = _to_utc(s["start"]).astimezone(tz)
            slots.append({"start": _to_utc(s["start"]).isoformat(), "label": local.strftime("%-I:%M %p")})
        if slots:
            first_local = _to_utc(day["slots"][0]["start"]).astimezone(tz)
            out.append({"date": day["date"], "date_label": first_local.strftime("%A, %b %-d"), "slots": slots})
    return {"service_id": service_id, "timezone": str(tz), "days": out}


class BookingRequest(BaseModel):
    service_id: int
    slot_start: str            # ISO 8601 UTC; must match an available slot
    name: str
    phone: str
    email: str
    street_address: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    problem_description: str | None = None
    company: str | None = None   # honeypot — real submissions leave this empty


@router.post("/embed/{slug}/book")
def create_booking(slug: str, body: BookingRequest, db: Session = Depends(get_db)):
    """Public booking creation. Re-validates the slot, books it, fires confirmation."""
    from app.models.customer import Customer
    from app.models.appointment import Appointment
    from app.services.notifications import _normalize_phone

    business = _get_business_or_404(slug, db)

    # Honeypot — bots fill hidden fields; accept silently and do nothing.
    if body.company:
        return {"booked": True, "message": "Thanks! Your request has been received."}

    if not (body.name and body.phone and body.email):
        raise HTTPException(status_code=422, detail="Name, phone, and email are required.")

    service = db.query(ServiceType).filter(
        ServiceType.id == body.service_id,
        ServiceType.business_id == business.id,
        ServiceType.is_active == True,
    ).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found.")
    if (service.category or "") == "Emergency":
        raise HTTPException(status_code=400, detail="Emergency service cannot be booked online — please call us.")

    try:
        start = _to_utc(datetime.fromisoformat(body.slot_start.replace("Z", "+00:00")))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid slot_start.")
    end = start + timedelta(minutes=service.duration_minutes)

    # Re-validate the slot is still genuinely open (hours, lead time, blocks, conflicts).
    tz = _biz_tz(business)
    local_date = start.astimezone(tz).date()
    avail = get_available_slots(db, business.id, body.service_id, local_date, local_date)
    slot_ok = any(
        abs((_to_utc(s["start"]) - start).total_seconds()) < 60
        for day in avail for s in day["slots"]
    )
    if not slot_ok:
        raise HTTPException(status_code=409, detail="That time was just taken. Please pick another slot.")

    tech_id = auto_assign_technician(db, business.id, body.service_id, start, end)
    if tech_id is None:
        raise HTTPException(status_code=409, detail="No technician available for that time. Please pick another slot.")

    # Find or create customer by phone (skip soft-deleted).
    phone_e164 = _normalize_phone(body.phone)
    customer = db.query(Customer).filter(
        Customer.business_id == business.id,
        Customer.phone == phone_e164,
        Customer.deleted_at == None,
    ).first()
    if not customer:
        parts = body.name.strip().split(None, 1)
        customer = Customer(
            business_id=business.id,
            first_name=parts[0],
            last_name=parts[1] if len(parts) > 1 else "",
            phone=phone_e164,
            email=body.email or None,
        )
        db.add(customer)
        db.flush()
    elif body.email and not customer.email:
        customer.email = body.email

    addr_parts = [p for p in [body.street_address, body.city, body.state, body.zip_code] if p]
    address = ", ".join(addr_parts) if addr_parts else None
    if address and not customer.address:
        customer.address = address
        if body.city and not customer.city: customer.city = body.city
        if body.state and not customer.state: customer.state = body.state
        if body.zip_code and not customer.zip_code: customer.zip_code = body.zip_code
    db.flush()

    appt = Appointment(
        business_id=business.id,
        customer_id=customer.id,
        technician_id=tech_id,
        service_type_id=service.id,
        scheduled_start=start,
        scheduled_end=end,
        status="confirmed",
        source="booking_widget",
        address=address,
        problem_description=body.problem_description or None,
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)

    try:
        from app.services.notifications import send_confirmation
        send_confirmation(db, appt)
    except Exception as exc:
        logger.warning("booking widget: confirmation failed for appt %s: %s", appt.id, exc)

    local = start.astimezone(tz)
    when = local.strftime("%A, %b %-d at %-I:%M %p")
    return {
        "booked": True,
        "appointment_id": appt.id,
        "scheduled_start": start.isoformat(),
        "when_label": when,
        "service": service.name,
        "message": "You're booked for {} on {}.".format(service.name, when),
    }


BOOKING_HTML = '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8" />\n<meta name="viewport" content="width=device-width, initial-scale=1.0" />\n<title>Book with __BIZNAME__</title>\n<style>\n*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}\nbody{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;font-size:14px;color:#111827;background:transparent;padding:16px;}\n.title{font-size:18px;font-weight:700;color:__BRAND__;margin-bottom:4px;}\n.sub{font-size:13px;color:#6b7280;margin-bottom:16px;}\n.step{margin-bottom:16px;}\n.step.hidden{display:none;}\nlabel{display:block;font-size:13px;font-weight:600;color:#374151;margin-bottom:5px;}\nlabel .req{color:#ef4444;margin-left:2px;}\nselect,input,textarea{width:100%;padding:8px 12px;border:1px solid #d1d5db;border-radius:6px;font-size:14px;color:#111827;background:#fff;outline:none;transition:border-color .15s,box-shadow .15s;}\nselect:focus,input:focus,textarea:focus{border-color:__BRAND__;box-shadow:0 0 0 3px __BRAND__22;}\ntextarea{resize:vertical;min-height:64px;}\n.chips{display:flex;flex-wrap:wrap;gap:8px;}\n.chip{padding:8px 12px;border:1px solid #d1d5db;border-radius:8px;background:#fff;font-size:13px;font-weight:600;color:#374151;cursor:pointer;transition:all .12s;}\n.chip:hover{border-color:__BRAND__;}\n.chip.sel{background:__BRAND__;color:#fff;border-color:__BRAND__;}\n.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;}\n.grid .full{grid-column:1/-1;}\n.fg{display:flex;flex-direction:column;}\n.fg label{margin-bottom:4px;}\n.muted{font-size:12px;color:#9ca3af;}\n.note{font-size:12px;color:#6b7280;margin-top:6px;}\n.btn{width:100%;padding:11px;background:__BRAND__;color:#fff;border:none;border-radius:8px;font-size:15px;font-weight:700;cursor:pointer;transition:opacity .15s;margin-top:6px;}\n.btn:hover{opacity:.9;}\n.btn:disabled{opacity:.6;cursor:not-allowed;}\n.alert{padding:10px 14px;border-radius:6px;font-size:13px;margin-bottom:12px;display:none;}\n.alert.error{background:#fef2f2;border:1px solid #fecaca;color:#991b1b;}\n.success{text-align:center;padding:32px 12px;display:none;}\n.success .ck{font-size:46px;margin-bottom:10px;}\n.success h3{font-size:18px;font-weight:700;color:__BRAND__;margin-bottom:8px;}\n.success p{color:#6b7280;font-size:14px;line-height:1.6;}\n.hp{position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden;}\n@media(max-width:480px){.grid{grid-template-columns:1fr;}.grid .full{grid-column:1;}}\n</style>\n</head>\n<body>\n<div id="root">\n  <div class="title">Book an appointment</div>\n  <div class="sub">with __BIZNAME__</div>\n  <div id="err" class="alert error"></div>\n\n  <div class="step" id="step-service">\n    <label for="svc">Service <span class="req">*</span></label>\n    <select id="svc"><option value="">Loading services…</option></select>\n  </div>\n\n  <div class="step hidden" id="step-date">\n    <label>Pick a day <span class="req">*</span></label>\n    <div class="chips" id="days"></div>\n    <div class="note" id="days-empty" style="display:none;">No open times in this window. Please call us.</div>\n  </div>\n\n  <div class="step hidden" id="step-time">\n    <label>Pick a time <span class="req">*</span></label>\n    <div class="chips" id="slots"></div>\n  </div>\n\n  <div class="step hidden" id="step-details">\n    <label style="font-size:14px;font-weight:700;color:#111827;">Your details</label>\n    <div class="grid">\n      <div class="fg"><label for="f-name">Full name <span class="req">*</span></label><input id="f-name" placeholder="Jane Smith" /></div>\n      <div class="fg"><label for="f-phone">Phone <span class="req">*</span></label><input id="f-phone" type="tel" placeholder="(321) 555-0100" /></div>\n      <div class="fg full"><label for="f-email">Email <span class="req">*</span></label><input id="f-email" type="email" placeholder="jane@example.com" /></div>\n      <div class="fg full"><label for="f-addr">Service address</label><input id="f-addr" placeholder="123 Main St" /></div>\n      <div class="fg"><label for="f-city">City</label><input id="f-city" placeholder="Cocoa" /></div>\n      <div class="fg"><label for="f-state">State</label><input id="f-state" placeholder="FL" maxlength="2" style="text-transform:uppercase;" /></div>\n      <div class="fg"><label for="f-zip">Zip</label><input id="f-zip" placeholder="32922" maxlength="10" /></div>\n      <div class="fg"><label for="f-problem">Describe the problem <span class="muted">(optional)</span></label><input id="f-problem" maxlength="200" placeholder="Any details help" /></div>\n      <div class="hp"><label>Company</label><input id="f-company" tabindex="-1" autocomplete="off" /></div>\n    </div>\n    <button class="btn" id="submit">Confirm booking</button>\n  </div>\n</div>\n\n<div class="success" id="success">\n  <div class="ck">✅</div>\n  <h3>You\'re booked!</h3>\n  <p id="success-msg"></p>\n</div>\n\n<script>\nconst SLUG = "__SLUG__";\nconst API  = "__APIBASE__";\nlet SERVICES=[], SEL_SERVICE=null, DAYS=[], SEL_SLOT=null;\n\nconst $ = id => document.getElementById(id);\nfunction showErr(m){ const e=$("err"); e.textContent=m; e.style.display="block"; }\nfunction clrErr(){ $("err").style.display="none"; }\nfunction resize(){ try{ window.parent.postMessage({type:"scs_booking_resize",height:document.body.scrollHeight},"*"); }catch(e){} }\n\nasync function init(){\n  try{\n    const r = await fetch(API+"/embed/"+SLUG+"/booking-config");\n    if(!r.ok) throw new Error();\n    const cfg = await r.json();\n    SERVICES = cfg.services||[];\n    const sel = $("svc");\n    sel.innerHTML = \'<option value="">— Select a service —</option>\';\n    SERVICES.forEach(s=>{\n      const dur = s.duration_minutes ? s.duration_minutes+" min" : "";\n      const price = (s.price!=null) ? " · $"+Math.round(s.price) : "";\n      const o=document.createElement("option"); o.value=s.id; o.textContent=s.name+(dur?(" ("+dur+price+")"):"");\n      sel.appendChild(o);\n    });\n    if(SERVICES.length===0){ sel.innerHTML=\'<option>No services available — please call us.</option>\'; }\n  }catch(e){ showErr("Could not load booking options. Please try again or call us."); }\n  resize();\n}\n\n$("svc").addEventListener("change", async function(){\n  clrErr(); SEL_SLOT=null;\n  $("step-time").classList.add("hidden"); $("step-details").classList.add("hidden");\n  const id=this.value; if(!id){ $("step-date").classList.add("hidden"); resize(); return; }\n  SEL_SERVICE=id;\n  $("days").innerHTML=\'<span class="muted">Loading availability…</span>\';\n  $("step-date").classList.remove("hidden");\n  try{\n    const r=await fetch(API+"/embed/"+SLUG+"/availability?service_id="+id+"&days=14");\n    const data=await r.json(); DAYS=data.days||[];\n    renderDays();\n  }catch(e){ showErr("Could not load availability."); }\n  resize();\n});\n\nfunction renderDays(){\n  const box=$("days"); box.innerHTML="";\n  if(DAYS.length===0){ $("days-empty").style.display="block"; resize(); return; }\n  $("days-empty").style.display="none";\n  DAYS.forEach((d,i)=>{\n    const c=document.createElement("div"); c.className="chip"; c.textContent=d.date_label;\n    c.onclick=()=>{ document.querySelectorAll("#days .chip").forEach(x=>x.classList.remove("sel")); c.classList.add("sel"); renderSlots(i); };\n    box.appendChild(c);\n  });\n}\n\nfunction renderSlots(dayIdx){\n  SEL_SLOT=null; $("step-details").classList.add("hidden");\n  const day=DAYS[dayIdx]; const box=$("slots"); box.innerHTML="";\n  day.slots.forEach(s=>{\n    const c=document.createElement("div"); c.className="chip"; c.textContent=s.label;\n    c.onclick=()=>{ document.querySelectorAll("#slots .chip").forEach(x=>x.classList.remove("sel")); c.classList.add("sel"); SEL_SLOT=s.start; $("step-details").classList.remove("hidden"); resize(); };\n    box.appendChild(c);\n  });\n  $("step-time").classList.remove("hidden"); resize();\n}\n\n$("submit").addEventListener("click", async function(){\n  clrErr();\n  const name=$("f-name").value.trim(), phone=$("f-phone").value.trim(), email=$("f-email").value.trim();\n  if(!SEL_SERVICE||!SEL_SLOT){ showErr("Please pick a service and time."); return; }\n  if(!name||!phone||!email){ showErr("Name, phone, and email are required."); return; }\n  this.disabled=true; this.textContent="Booking…";\n  const payload={\n    service_id:parseInt(SEL_SERVICE), slot_start:SEL_SLOT, name:name, phone:phone, email:email,\n    street_address:$("f-addr").value.trim()||null, city:$("f-city").value.trim()||null,\n    state:($("f-state").value.trim().toUpperCase())||null, zip_code:$("f-zip").value.trim()||null,\n    problem_description:$("f-problem").value.trim()||null, company:$("f-company").value.trim()||null\n  };\n  try{\n    const r=await fetch(API+"/embed/"+SLUG+"/book",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});\n    const data=await r.json().catch(()=>({}));\n    if(!r.ok){ throw new Error(data.detail||"Something went wrong. Please try another time."); }\n    $("root").style.display="none";\n    $("success-msg").textContent=data.message||"Your appointment is confirmed. We\'ll send a confirmation shortly.";\n    $("success").style.display="block";\n    try{ window.parent.postMessage({type:"scs_booking_submitted"},"*"); }catch(e){}\n    resize();\n  }catch(err){\n    showErr(err.message);\n    this.disabled=false; this.textContent="Confirm booking";\n    // If the slot was taken, refresh availability\n    if(/taken|available/i.test(err.message)){ $("svc").dispatchEvent(new Event("change")); }\n  }\n});\n\ninit();\n</script>\n</body>\n</html>'


@router.get("/embed/{slug}/booking", response_class=HTMLResponse)
def booking_embed(slug: str, db: Session = Depends(get_db)):
    """Self-contained, embeddable self-scheduling booking widget."""
    business = _get_business_or_404(slug, db)
    api_base = "https://api.spacecoaststudios.com"
    html = (
        BOOKING_HTML
        .replace("__BRAND__", business.brand_color or "#2563eb")
        .replace("__BIZNAME__", business.name)
        .replace("__APIBASE__", api_base)
        .replace("__SLUG__", slug)
    )
    return HTMLResponse(content=html, status_code=200, headers={"Cache-Control": "no-store"})
