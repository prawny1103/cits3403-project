from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# Initialize database
db = SQLAlchemy()
# Initialize CSRF protection
csrf = CSRFProtect()
# Initialize login manager
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
