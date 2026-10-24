"""Demo card handling: format checks only. Card data is never stored, logged or returned."""
import re
import secrets
from datetime import date


def validate_card(name: str, number: str, expiry: str, cvv: str) -> list:
    errors = []
    if not 2 <= len((name or "").strip()) <= 60:
        errors.append("Enter the name on the card.")
    digits = re.sub(r"[\s-]", "", number or "")
    if not re.fullmatch(r"\d{13,19}", digits):
        errors.append("Card number must be 13 to 19 digits.")
    m = re.fullmatch(r"(\d{2})\s*/\s*(\d{2})", (expiry or "").strip())
    if not m or not 1 <= int(m.group(1)) <= 12:
        errors.append("Expiry must look like MM/YY.")
    else:
        today = date.today()
        if (2000 + int(m.group(2)), int(m.group(1))) < (today.year, today.month):
            errors.append("This card has expired.")
    if not re.fullmatch(r"\d{3,4}", cvv or ""):
        errors.append("CVV must be 3 or 4 digits.")
    return errors


def mock_charge() -> str:
    """Pretend to charge the card; returns only an authorisation reference."""
    return "CARD" + secrets.token_hex(4).upper()
