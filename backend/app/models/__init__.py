"""Import all models so they're registered with SQLAlchemy."""

from app.models.business import Business
from app.models.customer import Customer
from app.models.service_type import ServiceType
from app.models.technician import Technician
from app.models.business_hours import BusinessHours
from app.models.blocked_time import BlockedTime
from app.models.appointment import Appointment
from app.models.inquiry import InquiryLog
from app.models.contact_submission import ContactSubmission
from app.models.notification import NotificationLog
from app.models.admin_user import AdminUser
from app.models.system_settings import SystemSetting
from app.models.recurring_schedule import RecurringSchedule
from app.models.oncall import OnCallConfig, OnCallRotation, OnCallOverride

__all__ = [
    "Business",
    "Customer",
    "ServiceType",
    "Technician",
    "BusinessHours",
    "BlockedTime",
    "RecurringSchedule",
    "Appointment",
    "InquiryLog",
    "ContactSubmission",
    "NotificationLog",
    "AdminUser",
    "SystemSetting",
    "OnCallConfig",
    "OnCallRotation",
    "OnCallOverride",
]
