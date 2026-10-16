from celery import Celery, Task
from flask import Flask, jsonify
from flask_cors import CORS
from flask_security import Security

from config import Config
from extensions import db, mail
from models import user_datastore
from seed import seed_database
from utils import ValidationError, error


MIN_SECRET_LENGTH = 16
PLACEHOLDER_PREFIXES = ("change-me", "dev-", "your_", "secret", "test-only")
PLACEHOLDER_ADMIN_PASSWORDS = ("admin123", "change-this-admin-password")
MIN_ADMIN_PASSWORD_LENGTH = 12


def validate_secrets(config):
    """Raise RuntimeError when SECRET_KEY / SECURITY_PASSWORD_SALT are unsafe."""
    for name in ("SECRET_KEY", "SECURITY_PASSWORD_SALT"):
        value = config.get(name) or ""
        if not value:
            raise RuntimeError(
                f"{name} is not set. Copy backend/.env.example to backend/.env and set a long random value "
                '(generate one with: python -c "import secrets; print(secrets.token_hex(32))").'
            )
        if len(value) < MIN_SECRET_LENGTH or value.lower().startswith(PLACEHOLDER_PREFIXES):
            raise RuntimeError(
                f"{name} is a placeholder or too short (need {MIN_SECRET_LENGTH}+ random characters). "
                'Generate one with: python -c "import secrets; print(secrets.token_hex(32))"'
            )


def validate_admin_password(config):
    """Require a non-placeholder admin password for non-test deployments."""
    password = str(config.get("ADMIN_PASSWORD") or "")
    if password in PLACEHOLDER_ADMIN_PASSWORDS or len(password) < MIN_ADMIN_PASSWORD_LENGTH:
        raise RuntimeError(
            "ADMIN_PASSWORD is a placeholder or too short. Set a unique password of at least "
            f"{MIN_ADMIN_PASSWORD_LENGTH} characters in backend/.env before starting the app."
        )


def celery_init_app(app):
    """Initialize Celery with Flask application context support."""

    class FlaskTask(Task):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.Task = FlaskTask
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Fail fast: never run with a missing or placeholder signing secret.
    if not app.config.get("TESTING"):
        validate_secrets(app.config)
        validate_admin_password(app.config)

    db.init_app(app)
    mail.init_app(app)
    CORS(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        allow_headers=["Content-Type", "Authentication-Token"],
    )

    # ---- Flask-Security (token authentication + roles) ---------------------
    security = Security(app, user_datastore)

    @security.unauthn_handler
    def unauthenticated(*args, **kwargs):
        return error("Authentication token missing or invalid", 401)

    @security.unauthz_handler
    def unauthorized(*args, **kwargs):
        return error("You do not have permission to do this", 403)

    # ---- Blueprints -------------------------------------------------------
    from routes.admin import admin_bp
    from routes.auth import auth_bp
    from routes.user import user_bp

    for bp in (auth_bp, admin_bp, user_bp):
        app.register_blueprint(bp)

    # ---- JSON error handlers ----------------------------------------------
    @app.errorhandler(ValidationError)
    def handle_validation(err):
        return error(str(err), 400)

    @app.errorhandler(404)
    def handle_404(_):
        return error("Resource not found", 404)

    @app.errorhandler(405)
    def handle_405(_):
        return error("Method not allowed", 405)

    @app.errorhandler(500)
    def handle_500(_):
        db.session.rollback()
        return error("Internal server error", 500)

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    celery_init_app(app)

    with app.app_context():
        db.create_all()
        seed_database(app)

    return app


if __name__ == "__main__":
    create_app().run(debug=True, port=5000)
