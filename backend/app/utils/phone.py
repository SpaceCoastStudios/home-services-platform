"""Phone number formatting helpers."""

import re


def format_phone_display(number):
    """Format a US phone number for customer-facing display: (321) 386-7604.

    Accepts E.164 (+13213867604), 11-digit (13213867604), or 10-digit
    (3213867604). Returns the original value unchanged if it is empty or not a
    parseable US 10-digit number (e.g. international numbers).
    """
    if not number:
        return number
    digits = re.sub(r"\D", "", str(number))
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) == 10:
        return "({}) {}-{}".format(digits[0:3], digits[3:6], digits[6:])
    return number
