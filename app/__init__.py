import os
from flask import Flask
from flask_socketio import SocketIO
from app.extensions import db, login_manager, csrf
from app.models import db, Question
from config import Config
import json

# Initialize websocket
socketio = SocketIO(cors_allowed_origins="*")

# The Flask factory function
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Connect the database and login manager to the app
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Connect socketio (websockets) to the app
    socketio.init_app(app)

    with app.app_context():
        from . import socket_events
        socket_events.init_app(app)
        db.create_all()
        if Question.query.count() == 0:
            sample_questions = [
                Question(text="What is the capital of France?", correct_answer="A", 
                        choices=json.dumps({"A": "Paris", "B": "London", "C": "Berlin", "D": "Madrid"}))
            ]
            db.session.add_all(sample_questions)
            db.session.commit()

    # Register Blueprints
    from app.routes.main import main_bp
    from app.routes.quiz import quiz_bp
    from app.routes.auth import auth_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(quiz_bp)
    app.register_blueprint(auth_bp)

    return app