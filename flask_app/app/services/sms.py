"""SmsService interface and a mock that writes to the SmsLog outbox (swap in Africa's Talking later)."""
from flask import current_app

from ..extensions import db
from ..models import Member, SmsLog


class SmsService:
    """Interface. A real implementation would call Africa's Talking inside send()."""

    def send(self, member, body, kind, created_at=None):
        raise NotImplementedError


class MockSmsService(SmsService):
    def send(self, member, body, kind, created_at=None):
        row = SmsLog(member_id=member.id, to_phone=member.phone, body=body[:320], kind=kind, status="sent")
        if created_at:
            row.created_at = created_at
        db.session.add(row)
        return row


def get_sms_service() -> SmsService:
    return current_app.extensions["sms_service"]


def notify_all(chama, body, kind, created_at=None):
    sms = get_sms_service()
    for m in chama.members:
        sms.send(m, body, kind, created_at)


def notify_members(members, body, kind):
    sms = get_sms_service()
    for m in members:
        sms.send(m, body, kind)


def notify_signatories(chama, body, kind="fraud_alert"):
    notify_members([m for m in chama.members if m.role == "signatory"], body, kind)
