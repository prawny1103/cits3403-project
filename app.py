from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = 'replace-this-with-a-secure-secret' # Do later, for now just a placeholder but when we change it we have to use the secret key in Github
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Stores user login information.
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Stores quiz room information.
class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_code = db.Column(db.String(10), unique=True, nullable=False)
    host_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(20), default="waiting")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Links users to rooms.
class RoomPlayer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

# Represents one quiz game session.
class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)

# Stores each player's result for a game.
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

@app.context_processor
def inject_current_user():
    user_id = session.get('user_id')
    if user_id:
        user = db.session.get(User, user_id)
    else:
        user = None
    return {'current_user': user}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def signup():
    if session.get('user_id'):
        return redirect(url_for('profile'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not username or not email or not password:
            flash('Please complete all required fields.')
            return redirect(url_for('signup'))

        if User.query.filter_by(username=username).first():
            flash('That username is already taken. Please choose another.')
            return redirect(url_for('signup'))

        if User.query.filter_by(email=email).first():
            flash('That email is already registered. Please log in.')
            return redirect(url_for('login'))

        password_hash = generate_password_hash(password)
        user = User(username=username, email=email, password_hash=password_hash)
        db.session.add(user)
        db.session.commit()

        session['user_id'] = user.id
        flash('Account created successfully. You are now logged in.')
        return redirect(url_for('profile'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        return redirect(url_for('profile'))

    if request.method == 'POST':
        login_value = request.form.get('login', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter((User.username == login_value) | (User.email == login_value)).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            flash('Signed in successfully.')
            return redirect(url_for('profile'))

        flash('Invalid username/email or password.')
        return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been signed out.')
    return redirect(url_for('home'))

@app.route('/profile')
def profile():
    user_id = session.get('user_id')
    if not user_id:
        flash('Please sign in to view your profile.')
        return redirect(url_for('login'))

    user = db.session.get(User, user_id)
    stats = PlayerStats.query.filter_by(user_id=user_id).all()
    return render_template('profile.html', user=user, stats=stats)

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
