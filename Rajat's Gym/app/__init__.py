"""
SmartGym Application Factory
Supports Flask-SQLAlchemy + Flask-Login when installed,
falls back to raw sqlite3 when not.
"""
import os

# ── Try importing optional ORM/auth packages ──────────────────────────────────
try:
    from flask_sqlalchemy import SQLAlchemy
    from flask_login import LoginManager
    HAS_EXTENSIONS = True
except ImportError:
    HAS_EXTENSIONS = False

from flask import Flask

db = None
login_manager = None


def create_app(config_name='default'):
    global db, login_manager

    app = Flask(__name__)

    # Load config
    try:
        from config import config as cfg_map
        app.config.from_object(cfg_map.get(config_name, cfg_map['default']))
    except ImportError:
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'smartgym_rajat_secret_2024_xyz')
        db_url = os.environ.get('DATABASE_URL', '')
        if not db_url:
            db_url = f"sqlite:///{os.path.join(os.path.dirname(os.path.dirname(__file__)), 'smartgym.db')}"
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    if HAS_EXTENSIONS:
        db = SQLAlchemy(app)
        login_manager = LoginManager(app)
        login_manager.login_view = 'auth.login'
        login_manager.login_message_category = 'warning'

        from .models import User

        @login_manager.user_loader
        def load_user(user_id):
            return User.query.get(int(user_id))

        from .routes.auth import auth_bp
        from .routes.dashboard import dash_bp
        from .routes.admin import admin_bp
        from .routes.workout import workout_bp

        app.register_blueprint(auth_bp)
        app.register_blueprint(dash_bp)
        app.register_blueprint(admin_bp)
        app.register_blueprint(workout_bp)

        with app.app_context():
            db.create_all()
            _seed_admin_orm()

    return app


def _seed_admin_orm():
    """Create default admin account if none exists."""
    from .models import User
    from werkzeug.security import generate_password_hash
    if not User.query.filter_by(role='admin').first():
        admin = User(
            name='Admin',
            email='admin@gym.com',
            password=generate_password_hash('admin123'),
            role='admin',
        )
        db.session.add(admin)
        db.session.commit()


