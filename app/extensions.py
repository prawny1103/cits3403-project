from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Initialize database
db = SQLAlchemy()

# Initialize login manager
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
