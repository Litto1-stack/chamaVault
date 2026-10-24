"""MpesaService interface and a mock STK push (swap in Daraja later). No real money moves."""
import re
import secrets
from dataclasses import dataclass

from werkzeug.security import check_password_hash


def normalize_phone(raw: str):
    """Return 2547XXXXXXXX / 2541XXXXXXXX from common Kenyan formats, or None if invalid."""
    digits = re.sub(r"[\s\-()]", "", raw or "").lstrip("+")
    if re.fullmatch(r"0[17]\d{8}", digits):
        digits = "254" + digits[1:]
    return digits if re.fullmatch(r"254[17]\d{8}", digits) else None


@dataclass
class StkRequest:
    checkout_id: str
    phone: str
    amount: int


class MpesaService:
    def stk_push(self, phone: str, amount: int, reference: str) -> StkRequest:
        raise NotImplementedError

    def complete(self, request: StkRequest, member, pin: str):
        """Return an M-Pesa receipt code, or None if the PIN was wrong."""
        raise NotImplementedError


class MockMpesaService(MpesaService):
    def stk_push(self, phone, amount, reference):
        return StkRequest("ws_CO_" + secrets.token_hex(6).upper(), phone, amount)

    def complete(self, request, member, pin):
        # The "customer" types their PIN on the simulated phone prompt; it is checked, never stored.
        if not re.fullmatch(r"\d{4}", pin or "") or not check_password_hash(member.pin_hash, pin):
            return None
        return "MP" + secrets.token_hex(4).upper()


def get_mpesa_service() -> MpesaService:
    from flask import current_app
    return current_app.extensions["mpesa_service"]
