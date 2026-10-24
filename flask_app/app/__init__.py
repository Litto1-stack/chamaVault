"""App factory: wires config, database, CSRF, services, blueprints, filters and the scheduler."""
import os

from flask import Flask, g, render_template

from config import Config
from .extensions import csrf, db
from .timeutil import kes, to_nairobi


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    os.makedirs(os.path.join(app.root_path, "..", "instance"), exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)

    from .services.mpesa import MockMpesaService
    from .services.sms import MockSmsService
    from .services.vaulti import LlmCoach, LocalFaqCoach
    app.extensions["sms_service"] = MockSmsService()
    app.extensions["mpesa_service"] = MockMpesaService()
    local = LocalFaqCoach()
    app.extensions["vaulti_coach"] = LlmCoach(local) if app.config["VAULTI_BACKEND"] == "llm" else local

    from . import models  # noqa: F401  (registers tables)
    from .auth import load_viewer
    from .routes import all_blueprints
    for bp in all_blueprints:
        app.register_blueprint(bp)

    app.before_request(load_viewer)
    from . import charts
    app.jinja_env.globals.update(charts=charts, initials=charts.initials, avatar_color=charts.avatar_color)
    app.jinja_env.filters["kes"] = kes
    app.jinja_env.filters["nairobi"] = lambda dt, fmt="%d %b %Y, %H:%M": to_nairobi(dt).strftime(fmt)

    @app.context_processor
    def inject_globals():
        from .models import Chama
        return {"viewer": g.get("viewer"), "chama": Chama.query.first()}

    @app.errorhandler(403)
    def forbidden(_):
        return render_template("error.html", title="Not allowed",
                               message="Your current role can't do this. Use 'Viewing as' to switch."), 403

    @app.errorhandler(404)
    def not_found(_):
        return render_template("error.html", title="Not found", message="We couldn't find that page."), 404

    with app.app_context():
        db.create_all()

    if app.config["SCHEDULER_ENABLED"] and (not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true"):
        from .reminders import start_scheduler
        start_scheduler(app)
    return app

