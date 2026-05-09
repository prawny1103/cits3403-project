from app import create_app
from app.models import db, Question
import json

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        # Seed logic (Only runs if DB is empty)
        if Question.query.count() == 0:
            sample_questions = [
                Question(text="What is the capital of France?", correct_answer="A", 
                        choices=json.dumps({"A": "Paris", "B": "London", "C": "Berlin", "D": "Madrid"}))
            ]
            db.session.add_all(sample_questions)
            db.session.commit()
            
    app.run(debug=True)