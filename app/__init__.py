from flask import Flask
from dotenv import load_dotenv
from .admin.routes import admin_bp
from config import Config
from .extensions import db, login_manager, csrf


load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    csrf.init_app(app)

    db.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    from .public.routes import public_bp
    from .auth.routes import auth_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp)

    with app.app_context():
        from . import models
        db.create_all()

    return app