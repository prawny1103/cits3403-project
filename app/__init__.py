from flask import Flask
from app.extensions import db, login_manager
from app.models import db, Question
from config import Config
import json

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
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