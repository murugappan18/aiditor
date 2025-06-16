import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Set up logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "audit-app-secret-key-2024")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database - using SQLite for local storage
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///audit_system.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@app.context_processor
def utility_processor():
    def getattr_safe(obj, attr, default=False):
        return getattr(obj, attr, default)
    return dict(getattr=getattr_safe)


@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

with app.app_context():
    # Import models to ensure they're registered
    import models
    
    # Create all tables
    db.create_all()
    
    # Create default admin user if none exists
    from models import User, Role
    from werkzeug.security import generate_password_hash
    
    # Create roles
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        admin_role = Role(name='admin', description='Administrator')
        db.session.add(admin_role)
    
    user_role = Role.query.filter_by(name='user').first()
    if not user_role:
        user_role = Role(name='user', description='Regular User')
        db.session.add(user_role)
    
    # Create default admin user
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = User(
            username='admin',
            email='admin@audit.com',
            password_hash=generate_password_hash('admin123'),
            role=admin_role,
            is_active=True
        )
        db.session.add(admin_user)
    
    db.session.commit()

# Register blueprints
from routes import main_bp
from auth import auth_bp

app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
