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
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.business import Business
from app.models.service_type import ServiceType

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

    .consent-error {{
      font-size: 12px;
      color: #dc2626;
      margin-top: 4px;
      margin-left: 26px;
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
        <label>Preferred contact method</label>
        <div class="contact-method-group">
          <label><input type="radio" name="contact_method" value="call" checked /> Phone call</label>
          <label><input type="radio" name="contact_method" value="text" /> Text message</label>
          <label><input type="radio" name="contact_method" value="email" /> Email</label>
        </div>
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
        <div class="sms-consent-group">
          <label class="sms-consent-label">
            <input type="checkbox" id="smsConsent" name="sms_consent" required />
            <span>
              I agree to receive SMS messages from {business_name}, including appointment
              confirmations, reminders, and service-related notifications. Msg &amp; data
              rates may apply. Reply STOP to opt out at any time. Reply HELP for help.
              View our <a href="https://spacecoaststudios.com/terms" target="_blank" rel="noopener">Terms</a>
              and <a href="https://spacecoaststudios.com/privacy" target="_blank" rel="noopener">Privacy Policy</a>.
            </span>
          </label>
          <div id="consentError" class="consent-error" style="display:none;">
            Please agree to receive SMS messages to continue.
          </div>
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

      // Validate SMS consent checkbox
      const consentBox   = document.getElementById("smsConsent");
      const consentError = document.getElementById("consentError");
      if (!consentBox.checked) {{
        consentError.style.display = "block";
        return;
      }}
      consentError.style.display = "none";

      btn.disabled    = true;
      btn.textContent = "Sending…";
      errorAlert.style.display = "none";

      const contactMethod = document.querySelector('input[name="contact_method"]:checked')?.value || null;

      const problemText = document.getElementById("problemDescription").value.trim();

      const payload = {{
        name:                     document.getElementById("name").value.trim(),
        email:                    document.getElementById("email").value.trim(),
        phone:                    document.getElementById("phone").value.trim(),
        service_requested:        document.getElementById("service").value || null,
        preferred_contact_method: contactMethod,
        message:                  document.getElementById("message").value.trim(),
        problem_description:      problemText || null,
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

    return HTMLResponse(content=html, status_code=200)
