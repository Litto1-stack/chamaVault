"""Collects every route blueprint for the app factory."""
from .election_routes import bp as elections_bp
from .info_routes import bp as info_bp
from .ledger_routes import bp as ledger_bp
from .loans_routes import bp as loans_bp
from .main import bp as main_bp
from .members_routes import bp as members_bp
from .pay import bp as pay_bp
from .rotation_routes import bp as rotation_bp
from .score_routes import bp as score_bp
from .sms_routes import bp as sms_bp
from .vaulti_routes import bp as vaulti_bp

all_blueprints = [main_bp, ledger_bp, pay_bp, sms_bp, loans_bp, score_bp, vaulti_bp,
                  elections_bp, rotation_bp, members_bp, info_bp]
