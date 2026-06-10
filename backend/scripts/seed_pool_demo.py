"""
Provision the "Brevard Pool Pros" pool-service demo tenant via the production API.

Creates: business (slug brevard-pool-pros), business hours, 5 pool services,
2 technicians, 4 customers (fictional 555 numbers, no emails), and 3 weekly
recurring schedules. Does NOT generate recurring appointment instances and
does NOT create any appointments, so no notifications fire.

Safe to re-run: exits if the slug already exists.

Usage (from the backend/ directory):
    python scripts/seed_pool_demo.py --username admin --password YOURPASSWORD

Credentials can also be set via env vars SCS_ADMIN_USER / SCS_ADMIN_PASS.
If neither is provided, the script prompts (note: the password prompt is
hidden - the console may look frozen while it waits for you to type).
"""

import argparse
import json
import os
import sys
import getpass
import urllib.request
import urllib.error
from datetime import date, timedelta

API = "https://api.spacecoaststudios.com"


def call(method, path, body=None, token=None):
    req = urllib.request.Request(API + path, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        print("HTTP {0} on {1}: {2}".format(e.code, path, e.read().decode()[:300]))
        sys.exit(1)
    except Exception as e:
        print("Request failed on {0}: {1}".format(path, e))
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--username", default=os.environ.get("SCS_ADMIN_USER"))
    ap.add_argument("--password", default=os.environ.get("SCS_ADMIN_PASS"))
    args = ap.parse_args()

    username = args.username
    password = args.password
    if not username:
        username = input("Platform admin username [admin]: ").strip() or "admin"
    if not password:
        print("Enter password (input is HIDDEN - type it and press Enter):")
        password = getpass.getpass("Password: ")

    print("Logging in to {0} ...".format(API))
    tok = call("POST", "/api/auth/login", {"username": username, "password": password})["access_token"]
    print("Login OK")

    businesses = call("GET", "/api/businesses", token=tok)
    existing = [b for b in businesses if b.get("slug") == "brevard-pool-pros"]
    if existing:
        print("Tenant already exists (id={0}). Nothing to do.".format(existing[0]["id"]))
        return

    prompt = (
        "You are Marina, the AI assistant for Brevard Pool Pros, a pool and spa service company "
        "serving Brevard County, Florida. You help customers schedule service, set up recurring "
        "maintenance plans, and answer questions about pool care.\n\n"
        "SERVICES: Weekly pool cleaning and maintenance, equipment repair, chemical balancing, "
        "algae treatment (green pool recovery), and pool opening and closing.\n\n"
        "TONE: Friendly and knowledgeable. Many customers are busy homeowners who just want their "
        "pool to look great. Be helpful and easy to work with.\n\n"
        "RECURRING MAINTENANCE (most common inquiry):\n"
        "- Ask if the customer is looking for one-time or recurring service\n"
        "- For recurring: confirm pool size (approximate), current condition, and address\n"
        "- Offer to schedule a first visit and set up a weekly or bi-weekly recurring plan\n"
        "- Collect contact details and confirm\n\n"
        "ONE-TIME OR REPAIR REQUESTS:\n"
        "- Confirm the issue (green water, equipment not working, etc.) and address\n"
        "- Offer 2 available appointment slots\n"
        "- Collect contact details and confirm\n\n"
        "PRICING: Do not quote specific prices. Our technician will assess the pool and provide a "
        "quote on the first visit. For recurring service, say: \"Our tech will give you a "
        "maintenance quote after the initial visit.\"\n\n"
        "You are an AI assistant. For customers who prefer to speak with someone, provide our "
        "number: (321) 555-0163."
    )

    biz = call("POST", "/api/businesses", {
        "name": "Brevard Pool Pros",
        "slug": "brevard-pool-pros",
        "phone": "(321) 555-0163",
        "address": "1200 N Courtenay Pkwy, Merritt Island, FL 32953",
        "industry": "pool",
        "brand_color": "#0891b2",
        "plan": "launchpad",
        "is_demo": True,
        "ai_agent_name": "Marina",
        "ai_system_prompt": prompt,
    }, token=tok)
    bid = biz["id"]
    print("Business created, id =", bid)

    q = "?business_id={0}".format(bid)

    # Business hours: Mon-Fri 8-5, Sat 8-12, Sun closed
    hours = [{"day_of_week": d, "open_time": "08:00", "close_time": "17:00", "is_active": True} for d in range(5)]
    hours.append({"day_of_week": 5, "open_time": "08:00", "close_time": "12:00", "is_active": True})
    hours.append({"day_of_week": 6, "open_time": "08:00", "close_time": "12:00", "is_active": False})
    call("PUT", "/api/business-hours" + q, {"hours": hours}, token=tok)
    print("Business hours set (Mon-Fri 8-5, Sat 8-12, Sun closed)")

    services = [
        ("Weekly Pool Maintenance", "pool", "Recurring weekly cleaning: skim, brush, vacuum, empty baskets, test and balance chemicals.", 45, None),
        ("Pool Equipment Repair", "pool", "Diagnose and repair pumps, filters, heaters, salt systems, and automation equipment.", 60, None),
        ("Chemical Balancing", "pool", "Full water test and chemical balance. Includes chlorine, pH, alkalinity, and stabilizer adjustment.", 30, 79.0),
        ("Green Pool Recovery", "pool", "Algae treatment and full recovery for green or neglected pools. Includes shock, brush, and filter clean.", 90, None),
        ("Pool Opening / Closing", "pool", "Seasonal opening or closing service including equipment check and water balance.", 90, 149.0),
    ]
    sids = {}
    for name, cat, desc, dur, price in services:
        s = call("POST", "/api/services" + q, {
            "name": name, "category": cat, "description": desc,
            "duration_minutes": dur, "base_price": price,
        }, token=tok)
        sids[name] = s["id"]
    print("Services created:", len(sids))

    tids = {}
    for name, phone in [("Marco Reyes", "(321) 555-0171"), ("Jenna Holt", "(321) 555-0172")]:
        t = call("POST", "/api/technicians" + q, {"name": name, "phone": phone, "skills": ["pool"]}, token=tok)
        tids[name] = t["id"]
    print("Technicians created:", list(tids))

    cust_data = [
        ("Alan", "Johnson", "(321) 555-0301", "123 Banana River Dr", "Merritt Island", "FL", "32952"),
        ("Priya", "Patel", "(321) 555-0302", "88 Lagoon Ct", "Cocoa Beach", "FL", "32931"),
        ("Maria", "Garcia", "(321) 555-0303", "12 Dolphin Ave", "Satellite Beach", "FL", "32937"),
        ("Tom", "Whitfield", "(321) 555-0304", "400 A1A", "Indian Harbour Beach", "FL", "32937"),
    ]
    cids = {}
    for fn, ln, ph, addr, city, st, zc in cust_data:
        c = call("POST", "/api/customers" + q, {
            "first_name": fn, "last_name": ln, "phone": ph,
            "address": addr, "city": city, "state": st, "zip_code": zc,
        }, token=tok)
        cids[fn] = c["id"]
    print("Customers created:", len(cids))

    # Weekly recurring schedules; start next week, no instance generation triggered.
    start = (date.today() + timedelta(days=((7 - date.today().weekday()) % 7) + 1)).isoformat()
    recs = [
        (cids["Alan"], sids["Weekly Pool Maintenance"], tids["Marco Reyes"], 1, "09:00", "123 Banana River Dr, Merritt Island, FL 32952"),
        (cids["Priya"], sids["Weekly Pool Maintenance"], tids["Marco Reyes"], 1, "10:00", "88 Lagoon Ct, Cocoa Beach, FL 32931"),
        (cids["Maria"], sids["Weekly Pool Maintenance"], tids["Jenna Holt"], 2, "09:00", "12 Dolphin Ave, Satellite Beach, FL 32937"),
    ]
    for cid, sid, tid, dow, t, addr in recs:
        call("POST", "/api/recurring" + q, {
            "customer_id": cid, "service_type_id": sid, "technician_id": tid,
            "frequency": "weekly", "preferred_day_of_week": dow, "preferred_time": t,
            "start_date": start, "address": addr,
        }, token=tok)
    print("Recurring schedules created: 3 (weekly)")

    print()
    print("DONE. Verify the widgets:")
    print("  {0}/embed/brevard-pool-pros/contact".format(API))
    print("  {0}/embed/brevard-pool-pros/booking".format(API))


if __name__ == "__main__":
    main()
