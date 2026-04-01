"""
Seed script — populates the default demo business with sample services, technicians,
customers, and appointments for testing.

Run from the backend directory:
    py -3.12 seed_data.py
"""

import sys
import os

# Ensure app module is importable
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta, timezone
from app.database import SessionLocal, init_db
from app.models.business import Business
from app.models.service_type import ServiceType
from app.models.technician import Technician
from app.models.customer import Customer
from app.models.appointment import Appointment


def seed():
    init_db()
    db = SessionLocal()

    # ── Find or create the default demo business ───────────────
    business = db.query(Business).filter(Business.slug == "default").first()
    if not business:
        print("ERROR: Default business not found. Start the server first so seed_defaults() runs.")
        db.close()
        return

    bid = business.id
    print(f"Seeding data for business: '{business.name}' (id={bid})\n")

    # ── Services ──────────────────────────────────────────────
    services_data = [
        # Plumbing
        ("Plumbing Repair", "plumbing", "Fix leaks, drips, running toilets, and minor pipe issues", 60, 95.00),
        ("Drain Cleaning", "plumbing", "Clear clogged drains in kitchens, bathrooms, and main lines", 45, 120.00),
        ("Water Heater Service", "plumbing", "Inspection, maintenance, or repair of water heaters", 90, 150.00),
        ("Faucet/Fixture Install", "plumbing", "Install new faucets, showerheads, or bathroom fixtures", 60, 85.00),
        # Electrical
        ("Electrical Repair", "electrical", "Fix outlets, switches, breakers, and wiring issues", 60, 110.00),
        ("Ceiling Fan Install", "electrical", "Install or replace ceiling fans with wiring", 90, 130.00),
        ("Panel Upgrade", "electrical", "Upgrade electrical panel for increased capacity", 180, 350.00),
        ("Lighting Install", "electrical", "Install recessed lighting, fixtures, or outdoor lights", 60, 100.00),
        # HVAC
        ("AC Repair", "hvac", "Diagnose and repair air conditioning systems", 90, 125.00),
        ("Furnace Tune-Up", "hvac", "Annual furnace inspection and maintenance", 60, 89.00),
        ("Duct Cleaning", "hvac", "Full ductwork cleaning for improved air quality", 120, 200.00),
        ("Thermostat Install", "hvac", "Install or upgrade smart thermostat systems", 45, 75.00),
        # Cleaning
        ("Standard House Cleaning", "cleaning", "Full house cleaning — kitchen, bathrooms, floors, dusting", 120, 150.00),
        ("Deep Clean", "cleaning", "Intensive cleaning including behind appliances and inside cabinets", 180, 250.00),
        ("Move-In/Move-Out Clean", "cleaning", "Thorough cleaning for property transitions", 240, 325.00),
        # Landscaping
        ("Lawn Mowing", "landscaping", "Mow, edge, and blow for standard residential lot", 45, 55.00),
        ("Hedge Trimming", "landscaping", "Trim and shape hedges, shrubs, and small trees", 60, 75.00),
        ("Seasonal Cleanup", "landscaping", "Spring or fall yard cleanup — leaves, debris, bed prep", 120, 175.00),
        # General
        ("Handyman Service", "general", "General repairs, mounting, assembly, and odd jobs", 60, 85.00),
        ("Drywall Repair", "general", "Patch holes, cracks, and drywall damage", 60, 95.00),
    ]

    existing_services = db.query(ServiceType).filter(ServiceType.business_id == bid).count()
    if existing_services <= 0:
        for name, category, desc, duration, price in services_data:
            db.add(ServiceType(
                business_id=bid,
                name=name, category=category, description=desc,
                duration_minutes=duration, base_price=price, is_active=True,
            ))
        db.commit()
        print(f"  Added {len(services_data)} services")
    else:
        print(f"  Services already seeded ({existing_services} found)")

    # ── Technicians ───────────────────────────────────────────
    technicians_data = [
        ("Mike Rodriguez", "555-101-0001", "mike@homeservices.com", ["plumbing", "general"]),
        ("Sarah Chen", "555-101-0002", "sarah@homeservices.com", ["plumbing", "hvac"]),
        ("James Walker", "555-101-0003", "james@homeservices.com", ["electrical", "general"]),
        ("Emily Nguyen", "555-101-0004", "emily@homeservices.com", ["electrical"]),
        ("David Thompson", "555-101-0005", "david@homeservices.com", ["hvac"]),
        ("Maria Garcia", "555-101-0006", "maria@homeservices.com", ["cleaning"]),
        ("Lisa Park", "555-101-0007", "lisa@homeservices.com", ["cleaning"]),
        ("Carlos Rivera", "555-101-0008", "carlos@homeservices.com", ["landscaping", "general"]),
    ]

    existing_techs = db.query(Technician).filter(Technician.business_id == bid).count()
    if existing_techs <= 0:
        for name, phone, email, skills in technicians_data:
            db.add(Technician(
                business_id=bid,
                name=name, phone=phone, email=email, skills=skills, is_active=True,
            ))
        db.commit()
        print(f"  Added {len(technicians_data)} technicians")
    else:
        print(f"  Technicians already seeded ({existing_techs} found)")

    # ── Customers ─────────────────────────────────────────────
    customers_data = [
        ("John", "Miller", "555-200-1001", "john.miller@email.com", "742 Evergreen Terrace, Springfield", "62704"),
        ("Patricia", "Davis", "555-200-1002", "pat.davis@email.com", "1640 Riverside Drive, Hill Valley", "91331"),
        ("Robert", "Wilson", "555-200-1003", "rwilson@email.com", "31 Spooner Street, Quahog", "02907"),
        ("Jennifer", "Taylor", "555-200-1004", "jtaylor@email.com", "1725 Slough Ave, Scranton", "18503"),
        ("Michael", "Anderson", "555-200-1005", "m.anderson@email.com", "344 Clinton Street, Apt 3B", "10014"),
        ("Linda", "Martinez", "555-200-1006", "linda.m@email.com", "4848 Homestead Way", "85001"),
        ("William", "Brown", "555-200-1007", "wbrown@email.com", "221 Oak Lane", "30301"),
        ("Elizabeth", "Jones", "555-200-1008", "ejones@email.com", "88 Maple Court", "60601"),
        ("Richard", "Garcia", "555-200-1009", "rgarcia@email.com", "562 Pine Ridge Blvd", "75201"),
        ("Susan", "White", "555-200-1010", "swhite@email.com", "1010 Cedar Creek Dr", "97201"),
        ("Thomas", "Lee", "555-200-1011", "tlee@email.com", "403 Birch Street", "02101"),
        ("Karen", "Harris", "555-200-1012", "kharris@email.com", "77 Willow Way", "48201"),
    ]

    existing_customers = db.query(Customer).filter(Customer.business_id == bid).count()
    if existing_customers <= 0:
        for first, last, phone, email, address, zipcode in customers_data:
            db.add(Customer(
                business_id=bid,
                first_name=first, last_name=last, phone=phone,
                email=email, address=address, zip_code=zipcode,
            ))
        db.commit()
        print(f"  Added {len(customers_data)} customers")
    else:
        print(f"  Customers already seeded ({existing_customers} found)")

    # ── Sample Appointments ───────────────────────────────────
    existing_appts = db.query(Appointment).filter(Appointment.business_id == bid).count()
    if existing_appts <= 0:
        # Get IDs from DB, scoped to this business
        all_services = {s.name: s for s in db.query(ServiceType).filter(ServiceType.business_id == bid).all()}
        all_techs = {t.name: t for t in db.query(Technician).filter(Technician.business_id == bid).all()}
        all_customers = {
            f"{c.first_name} {c.last_name}": c
            for c in db.query(Customer).filter(Customer.business_id == bid).all()
        }

        now = datetime.now(timezone.utc)
        today_8am = now.replace(hour=8, minute=0, second=0, microsecond=0)

        appointments_data = [
            # Today's appointments
            ("John Miller", "Plumbing Repair", "Mike Rodriguez", today_8am + timedelta(hours=1), "confirmed"),
            ("Patricia Davis", "AC Repair", "David Thompson", today_8am + timedelta(hours=2), "confirmed"),
            ("Robert Wilson", "Electrical Repair", "James Walker", today_8am + timedelta(hours=3), "in_progress"),
            ("Jennifer Taylor", "Standard House Cleaning", "Maria Garcia", today_8am + timedelta(hours=1), "confirmed"),
            # Tomorrow
            ("Michael Anderson", "Drain Cleaning", "Sarah Chen", today_8am + timedelta(days=1, hours=1), "confirmed"),
            ("Linda Martinez", "Ceiling Fan Install", "Emily Nguyen", today_8am + timedelta(days=1, hours=2), "pending"),
            ("William Brown", "Lawn Mowing", "Carlos Rivera", today_8am + timedelta(days=1, hours=0), "confirmed"),
            # Day after tomorrow
            ("Elizabeth Jones", "Deep Clean", "Lisa Park", today_8am + timedelta(days=2, hours=1), "pending"),
            ("Richard Garcia", "Furnace Tune-Up", "David Thompson", today_8am + timedelta(days=2, hours=0), "pending"),
            ("Susan White", "Handyman Service", "Mike Rodriguez", today_8am + timedelta(days=2, hours=3), "pending"),
            # Past (completed)
            ("Thomas Lee", "Faucet/Fixture Install", "Mike Rodriguez", today_8am - timedelta(days=1, hours=-1), "completed"),
            ("Karen Harris", "Thermostat Install", "Sarah Chen", today_8am - timedelta(days=2, hours=-2), "completed"),
        ]

        count = 0
        for cust_name, svc_name, tech_name, start, status in appointments_data:
            customer = all_customers.get(cust_name)
            service = all_services.get(svc_name)
            tech = all_techs.get(tech_name)
            if customer and service and tech:
                db.add(Appointment(
                    business_id=bid,
                    customer_id=customer.id,
                    service_type_id=service.id,
                    technician_id=tech.id,
                    scheduled_start=start,
                    scheduled_end=start + timedelta(minutes=service.duration_minutes),
                    status=status,
                    source="dashboard",
                    address=customer.address,
                ))
                count += 1
        db.commit()
        print(f"  Added {count} sample appointments")
    else:
        print(f"  Appointments already seeded ({existing_appts} found)")

    db.close()
    print("\nDone! Refresh your dashboard to see the data.")


if __name__ == "__main__":
    print("Seeding database...\n")
    seed()
