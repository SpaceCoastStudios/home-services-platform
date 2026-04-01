"""
Seed script — creates the Peak HVAC demo tenant with realistic branding,
services, technicians, customers, and a mix of upcoming/past appointments.

Run from the backend directory AFTER the server has started at least once:
    py -3.12 seed_peak_hvac.py

Safe to run multiple times — checks for existing data before inserting.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta, time, timezone
from app.database import SessionLocal, init_db
from app.models.business import Business
from app.models.admin_user import AdminUser
from app.models.business_hours import BusinessHours
from app.models.system_settings import SystemSetting
from app.models.service_type import ServiceType
from app.models.technician import Technician
from app.models.customer import Customer
from app.models.appointment import Appointment
from app.utils.auth import hash_password


def seed():
    init_db()
    db = SessionLocal()

    # ── Business record ───────────────────────────────────────
    business = db.query(Business).filter(Business.slug == "peak-hvac").first()
    if not business:
        business = Business(
            name="Peak HVAC Services",
            slug="peak-hvac",
            phone="(321) 555-0142",
            email="info@peakhvac.com",
            address="4820 Merritt Island Cswy, Merritt Island, FL 32952",
            website="https://peakhvac.com",
            industry="hvac",
            plan="full",
            is_active=True,
            is_demo=True,
            brand_color="#e85d04",
            ai_agent_name="Max",
            ai_system_prompt=(
                "You are Max, a friendly scheduling assistant for Peak HVAC Services "
                "in Merritt Island, Florida. You help homeowners and businesses book "
                "HVAC service, repair, and maintenance appointments. Always be warm, "
                "professional, and helpful. When someone describes a problem, ask "
                "clarifying questions to match them with the right service. Mention "
                "that same-day appointments may be available. Never make up pricing — "
                "say a technician will provide a quote on arrival."
            ),
        )
        db.add(business)
        db.flush()
        print(f"  Created business: Peak HVAC Services (id={business.id})")
    else:
        print(f"  Business already exists (id={business.id})")

    bid = business.id

    # ── Business admin user ───────────────────────────────────
    existing_admin = db.query(AdminUser).filter(AdminUser.username == "peakhvac").first()
    if not existing_admin:
        admin = AdminUser(
            business_id=bid,
            username="peakhvac",
            password_hash=hash_password("hvac1234"),
            role="admin",
            is_active=True,
        )
        db.add(admin)
        print("  Created admin user: peakhvac / hvac1234")
    else:
        print("  Admin user already exists")

    # ── Business hours ────────────────────────────────────────
    existing_hours = db.query(BusinessHours).filter(BusinessHours.business_id == bid).first()
    if not existing_hours:
        # Mon-Fri 7am-6pm, Sat 8am-2pm, Sun closed
        for day in range(5):
            db.add(BusinessHours(business_id=bid, day_of_week=day,
                                 open_time=time(7, 0), close_time=time(18, 0), is_active=True))
        db.add(BusinessHours(business_id=bid, day_of_week=5,
                             open_time=time(8, 0), close_time=time(14, 0), is_active=True))
        # Sunday closed (is_active=False)
        db.add(BusinessHours(business_id=bid, day_of_week=6,
                             open_time=time(8, 0), close_time=time(12, 0), is_active=False))
        print("  Seeded business hours (Mon-Fri 7-6, Sat 8-2, Sun closed)")
    else:
        print("  Business hours already seeded")

    # ── System settings ───────────────────────────────────────
    existing_settings = db.query(SystemSetting).filter(SystemSetting.business_id == bid).first()
    if not existing_settings:
        settings = [
            ("slot_granularity_minutes", "30", "Time slot increment in minutes"),
            ("buffer_minutes", "15", "Buffer time between appointments in minutes"),
            ("max_advance_booking_days", "60", "How far in advance customers can book (days)"),
            ("min_lead_time_hours", "2", "Minimum hours before an appointment can be booked"),
            ("max_appointments_per_tech_per_day", "6", "Maximum appointments per technician per day"),
            ("allow_same_day_booking", "true", "Whether same-day appointments are allowed"),
        ]
        for key, value, desc in settings:
            db.add(SystemSetting(business_id=bid, key=key, value=value, description=desc))
        print("  Seeded scheduling settings")
    else:
        print("  Settings already seeded")

    db.commit()

    # ── Services ──────────────────────────────────────────────
    existing_services = db.query(ServiceType).filter(ServiceType.business_id == bid).count()
    if existing_services == 0:
        services_data = [
            # Diagnostics
            ("HVAC Diagnostic", "hvac",
             "Full system diagnostic to identify issues with heating or cooling performance.", 60, 89.00),
            # Cooling
            ("AC Repair", "hvac",
             "Diagnose and repair air conditioning systems — refrigerant issues, compressor, fan motors, and more.", 90, 0.00),
            ("AC Tune-Up & Maintenance", "hvac",
             "Seasonal AC tune-up including coil cleaning, refrigerant check, filter replacement, and full inspection.", 75, 119.00),
            ("AC Installation", "hvac",
             "Full installation of a new central air conditioning system, including line set, disconnect, and startup.", 240, 0.00),
            ("Mini-Split Installation", "hvac",
             "Install ductless mini-split system — single or multi-zone. Includes mounting, wiring, and refrigerant charge.", 180, 0.00),
            # Heating
            ("Furnace Repair", "hvac",
             "Diagnose and repair gas or electric furnace — igniter, heat exchanger, blower motor, and controls.", 90, 0.00),
            ("Furnace Tune-Up", "hvac",
             "Annual furnace inspection and tune-up including burner cleaning, heat exchanger check, and filter swap.", 60, 99.00),
            ("Heat Pump Service", "hvac",
             "Full heat pump inspection, refrigerant check, and servicing for heating and cooling operation.", 90, 119.00),
            # Air Quality & Ductwork
            ("Duct Cleaning", "hvac",
             "Comprehensive cleaning of all supply and return ducts to improve air quality and system efficiency.", 120, 249.00),
            ("Duct Repair / Sealing", "hvac",
             "Locate and seal duct leaks using mastic or foil tape. Improves efficiency and reduces energy bills.", 90, 0.00),
            ("Air Quality Assessment", "hvac",
             "Indoor air quality test including humidity, particulates, and CO2. Includes filter and UV light recommendations.", 45, 79.00),
            # Thermostats & Controls
            ("Smart Thermostat Install", "hvac",
             "Install and configure a smart thermostat (Nest, Ecobee, Honeywell). Includes wiring and app setup.", 60, 129.00),
            # Emergency
            ("Emergency Service Call", "hvac",
             "Priority same-day or after-hours response for heating or cooling emergencies.", 60, 149.00),
        ]
        for name, cat, desc, duration, price in services_data:
            db.add(ServiceType(
                business_id=bid, name=name, category=cat,
                description=desc, duration_minutes=duration,
                base_price=price if price > 0 else None,
                is_active=True,
            ))
        db.commit()
        print(f"  Added {len(services_data)} services")
    else:
        print(f"  Services already seeded ({existing_services} found)")

    # ── Technicians ───────────────────────────────────────────
    existing_techs = db.query(Technician).filter(Technician.business_id == bid).count()
    if existing_techs == 0:
        techs_data = [
            ("Brandon Cole",    "(321) 555-0201", "bcole@peakhvac.com",    ["hvac"], True),
            ("Stephanie Marsh", "(321) 555-0202", "smarsh@peakhvac.com",   ["hvac"], True),
            ("Derek Okafor",    "(321) 555-0203", "dokafor@peakhvac.com",  ["hvac"], True),
            ("Angela Tran",     "(321) 555-0204", "atran@peakhvac.com",    ["hvac"], True),
            ("Marcus Webb",     "(321) 555-0205", "mwebb@peakhvac.com",    ["hvac"], False),  # Inactive — on leave
        ]
        for name, phone, email, skills, is_active in techs_data:
            db.add(Technician(
                business_id=bid, name=name, phone=phone,
                email=email, skills=skills, is_active=is_active,
            ))
        db.commit()
        print(f"  Added {len(techs_data)} technicians (4 active, 1 inactive)")
    else:
        print(f"  Technicians already seeded ({existing_techs} found)")

    # ── Customers ─────────────────────────────────────────────
    existing_customers = db.query(Customer).filter(Customer.business_id == bid).count()
    if existing_customers == 0:
        customers_data = [
            # (first, last, phone, email, address, zip)
            ("Sandra",  "Morales",   "(321) 555-1101", "smorales@gmail.com",      "118 Flamingo Dr, Merritt Island, FL",   "32952"),
            ("James",   "Ostrowski", "(321) 555-1102", "jostrowski@outlook.com",  "54 Canaveral Blvd, Cocoa Beach, FL",    "32931"),
            ("Debra",   "Fountain",  "(321) 555-1103", "dfountain@yahoo.com",     "2201 S Atlantic Ave, Cocoa Beach, FL",  "32931"),
            ("Kevin",   "Hutchins",  "(321) 555-1104", "khutchins@gmail.com",     "407 Oak Park Dr, Titusville, FL",       "32780"),
            ("Lorraine","Castillo",  "(321) 555-1105", "lcastillo@gmail.com",     "39 Harbor Point Rd, Merritt Island, FL","32952"),
            ("Paul",    "Nguyen",    "(321) 555-1106", "pnguyen@icloud.com",      "1822 Banana River Dr, Merritt Island, FL","32952"),
            ("Tammy",   "Birch",     "(321) 555-1107", "tbirch@outlook.com",      "615 N Brevard Ave, Cocoa Beach, FL",    "32931"),
            ("Gregory", "Simmons",   "(321) 555-1108", "gsimmons@gmail.com",      "903 Dixon Blvd, Cocoa, FL",             "32922"),
            ("Christine","Yates",    "(321) 555-1109", "cyates@yahoo.com",        "2540 N Courtenay Pkwy, Merritt Island, FL","32953"),
            ("Robert",  "Delgado",   "(321) 555-1110", "rdelgado@gmail.com",      "77 Tropical Dr, Titusville, FL",        "32796"),
            ("Monica",  "Shaw",      "(321) 555-1111", "mshaw@gmail.com",         "310 Fortenberry Rd, Merritt Island, FL","32952"),
            ("Tyler",   "Henson",    "(321) 555-1112", "thenson@outlook.com",     "1140 N Banana River Dr, Merritt Island, FL","32952"),
            ("Diana",   "Kowalski",  "(321) 555-1113", "dkowalski@icloud.com",    "528 Orange Ave, Titusville, FL",        "32796"),
            ("Marcus",  "Fleming",   "(321) 555-1114", "mfleming@gmail.com",      "85 Kennedy Dr, Cape Canaveral, FL",     "32920"),
            ("Janet",   "Ruiz",      "(321) 555-1115", "jruiz@yahoo.com",         "2010 S Banana River Blvd, Cocoa Beach, FL","32931"),
        ]
        for first, last, phone, email, address, zipcode in customers_data:
            db.add(Customer(
                business_id=bid, first_name=first, last_name=last,
                phone=phone, email=email, address=address, zip_code=zipcode,
            ))
        db.commit()
        print(f"  Added {len(customers_data)} customers")
    else:
        print(f"  Customers already seeded ({existing_customers} found)")

    # ── Appointments ──────────────────────────────────────────
    existing_appts = db.query(Appointment).filter(Appointment.business_id == bid).count()
    if existing_appts == 0:
        all_services = {s.name: s for s in db.query(ServiceType).filter(ServiceType.business_id == bid).all()}
        all_techs    = {t.name: t for t in db.query(Technician).filter(Technician.business_id == bid, Technician.is_active == True).all()}
        all_customers = {f"{c.first_name} {c.last_name}": c for c in db.query(Customer).filter(Customer.business_id == bid).all()}

        now = datetime.now(timezone.utc)
        # Anchor to 8am today
        today = now.replace(hour=8, minute=0, second=0, microsecond=0)

        # (customer_name, service_name, tech_name, time_delta, status, notes)
        appts_data = [
            # ── Past completed ────────────────────────────────
            ("Sandra Morales",   "AC Tune-Up & Maintenance", "Brandon Cole",
             timedelta(days=-14, hours=0), "completed",
             "Cleaned coils, replaced filter, checked refrigerant — system in good shape."),

            ("James Ostrowski",  "Furnace Repair",           "Stephanie Marsh",
             timedelta(days=-10, hours=2), "completed",
             "Replaced igniter and cleaned burners. Heat exchanger looks fine."),

            ("Debra Fountain",   "Smart Thermostat Install", "Derek Okafor",
             timedelta(days=-8, hours=1),  "completed",
             "Installed Ecobee SmartThermostat. Customer set up app on-site."),

            ("Kevin Hutchins",   "AC Repair",                "Brandon Cole",
             timedelta(days=-7, hours=0),  "completed",
             "Low refrigerant — added 2 lbs R-410A. Found small leak at Schrader valve, replaced."),

            ("Lorraine Castillo","Duct Cleaning",            "Angela Tran",
             timedelta(days=-5, hours=1),  "completed",
             "Full duct cleaning — significant buildup in master bedroom supply runs."),

            ("Paul Nguyen",      "HVAC Diagnostic",          "Stephanie Marsh",
             timedelta(days=-3, hours=3),  "completed",
             "Intermittent cooling issue — traced to failing capacitor. Replaced same visit."),

            ("Tammy Birch",      "Heat Pump Service",        "Derek Okafor",
             timedelta(days=-2, hours=0),  "completed",
             "Annual service completed. Refrigerant charge nominal, contactor shows wear — recommend replacement next visit."),

            # ── Yesterday ─────────────────────────────────────
            ("Gregory Simmons",  "AC Tune-Up & Maintenance", "Brandon Cole",
             timedelta(days=-1, hours=1),  "completed",
             "Tune-up complete. Recommended UV air purifier for next visit."),

            ("Christine Yates",  "Emergency Service Call",   "Angela Tran",
             timedelta(days=-1, hours=3),  "completed",
             "AC stopped cooling — found tripped breaker and failed run capacitor. Replaced capacitor, system running."),

            # ── Today ─────────────────────────────────────────
            ("Robert Delgado",   "Furnace Tune-Up",          "Stephanie Marsh",
             timedelta(hours=0),           "confirmed",
             "Annual furnace tune-up before winter season."),

            ("Monica Shaw",      "AC Repair",                "Brandon Cole",
             timedelta(hours=2),           "in_progress",
             "Customer reports warm air blowing — technician en route."),

            ("Tyler Henson",     "HVAC Diagnostic",          "Derek Okafor",
             timedelta(hours=4),           "confirmed",
             "New customer — system is 11 years old, poor cooling upstairs."),

            # ── Tomorrow ──────────────────────────────────────
            ("Diana Kowalski",   "AC Tune-Up & Maintenance", "Angela Tran",
             timedelta(days=1, hours=0),   "confirmed",
             ""),

            ("Marcus Fleming",   "Smart Thermostat Install", "Brandon Cole",
             timedelta(days=1, hours=2),   "confirmed",
             "Customer purchased Nest Thermostat — needs wiring for 3rd-party unit."),

            ("Janet Ruiz",       "Duct Repair / Sealing",    "Stephanie Marsh",
             timedelta(days=1, hours=1),   "confirmed",
             "High energy bills — possible duct leaks in attic."),

            # ── Later this week ───────────────────────────────
            ("Sandra Morales",   "Air Quality Assessment",   "Derek Okafor",
             timedelta(days=2, hours=3),   "pending",
             "Follow-up from AC tune-up — customer interested in UV air purifier."),

            ("Kevin Hutchins",   "AC Tune-Up & Maintenance", "Brandon Cole",
             timedelta(days=3, hours=0),   "pending",
             ""),

            ("Lorraine Castillo","Smart Thermostat Install", "Angela Tran",
             timedelta(days=3, hours=2),   "pending",
             "Upgrading from old Honeywell to Ecobee — customer already purchased unit."),

            ("Paul Nguyen",      "Furnace Tune-Up",          "Stephanie Marsh",
             timedelta(days=4, hours=1),   "pending",
             ""),

            ("Tammy Birch",      "Heat Pump Service",        "Derek Okafor",
             timedelta(days=5, hours=0),   "pending",
             "Recommended contactor replacement from last visit."),
        ]

        count = 0
        for cust_name, svc_name, tech_name, delta, status, notes in appts_data:
            customer = all_customers.get(cust_name)
            service  = all_services.get(svc_name)
            tech     = all_techs.get(tech_name)
            if not (customer and service and tech):
                print(f"  WARNING: Could not match '{cust_name}' / '{svc_name}' / '{tech_name}' — skipping")
                continue
            start = today + delta
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
                notes=notes or None,
            ))
            count += 1

        db.commit()
        print(f"  Added {count} appointments (9 past, 2 yesterday, 3 today, 3 tomorrow, 3 this week)")
    else:
        print(f"  Appointments already seeded ({existing_appts} found)")

    db.close()
    print("\nDone! Log into the dashboard, select 'Peak HVAC Services', and explore.")
    print("Business admin login:  peakhvac / hvac1234")


if __name__ == "__main__":
    print("Seeding Peak HVAC demo tenant...\n")
    seed()
