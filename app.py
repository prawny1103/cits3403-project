from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_code = db.Column(db.String(10), unique=True, nullable=False)
    host_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(20), default="waiting")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class RoomPlayer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
    started_at = db.Column(db.DateTime)
    ended_at = db.Column(db.DateTime)


class PlayerStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    score = db.Column(db.Integer)
    correct_answers = db.Column(db.Integer)


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    correct_answer = db.Column(db.String(10), nullable=False)  # For multiple choice: A, B, C, D
    question_type = db.Column(db.String(20), default="multiple_choice")  # multiple_choice, true_false, etc.
    choices = db.Column(db.Text, nullable=True)  # JSON string of choices: {"A": "Paris", "B": "London", "C": "Berlin", "D": "Madrid"}
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register')
def signup():
    return render_template('signup.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/about')
def about():
    return render_template('contactUs.html')

@app.route('/friends')
def friends():
    return render_template('friends.html')

@app.route('/multichoice')
def multichoice():
    # Get the first question or a specific question by ID
    question_id = request.args.get('question_id', 1, type=int)
    question = db.session.get(Question, question_id)
    if not question:
        return "Question not found", 404
    
    choices = json.loads(question.choices) if question.choices else {}
    return render_template('multichoice.html', question=question.text, question_id=question.id, choices=choices)


@app.route('/get-next-question')
def get_next_question():
    current_id = request.args.get('current_id', 0, type=int)
    next_question = Question.query.filter(Question.id > current_id).first()
    if next_question:
        choices = json.loads(next_question.choices) if next_question.choices else {}
        return jsonify({
            'id': next_question.id,
            'text': next_question.text,
            'choices': choices,
            'has_next': Question.query.filter(Question.id > next_question.id).first() is not None
        })
    else:
        return jsonify({'finished': True})

@app.route('/check-answer', methods=['POST'])
def check_answer():
    data = request.get_json()
    q_id = data.get('question_id')
    user_choice = data.get('user_choice')

    question = db.session.get(Question, q_id)
    if not question:
        return jsonify({"error": "Question not found"}), 404

    is_correct = user_choice == question.correct_answer
    return jsonify({
        "is_correct": is_correct
    })

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        # Add sample questions if none exist
        if Question.query.count() == 0:
            sample_questions = [
                Question(text="What is the capital of France?", correct_answer="A", 
                        choices=json.dumps({"A": "Paris", "B": "London", "C": "Berlin", "D": "Madrid"})),
                Question(text="Which planet is known as the Red Planet?", correct_answer="B", 
                        choices=json.dumps({"A": "Venus", "B": "Mars", "C": "Jupiter", "D": "Saturn"})),
                Question(text="What is 2 + 2?", correct_answer="B", 
                        choices=json.dumps({"A": "3", "B": "4", "C": "400", "D": "5"})),
                Question(text="Who wrote Romeo and Juliet?", correct_answer="D", 
                        choices=json.dumps({"A": "Charles Dickens", "B": "Jane Austen", "C": "Mark Twain", "D": "William Shakespeare"})),
                Question(text="What is the largest ocean on Earth?", correct_answer="A", 
                        choices=json.dumps({"A": "Pacific Ocean", "B": "Atlantic Ocean", "C": "Indian Ocean", "D": "Arctic Ocean"}))
            ]
            db.session.add_all(sample_questions)
            db.session.commit()
    app.run(debug=True)
