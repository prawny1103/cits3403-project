from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

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
    question = "The sky is blue?"
    return render_template('multichoice.html', question=question, question_id=1)

@app.route('/check-answer', methods=['POST'])
def check_answer():
    data = request.get_json()
    q_id = data.get('question_id')
    user_choice = data.get('user_choice')

    # Perform database lookup to see if the user choice is the correct choice for the question id
    # Perform logic based on whether correct or nots

    correct_answer = 'C' # pretend this was found from the database
    if user_choice == correct_answer:
        return jsonify({
            "is_correct": True
        })
    else:
        return jsonify({
            "is_correct": False
        })

if __name__ == "__main__":
    app.run(debug=True)
