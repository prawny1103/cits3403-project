from flask import Flask
from app.extensions import db, login_manager
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    # Register Blueprints
    from app.routes.main import main_bp
    from app.routes.quiz import quiz_bp
    from app.routes.auth import auth_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(quiz_bp)
    app.register_blueprint(auth_bp)

    return app