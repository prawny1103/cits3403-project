from datetime import datetime
import json
import random
import string
from app.extensions import db

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_code = db.Column(db.String(4), nullable=False) # room code is not unique, can be reused when room ends
    is_active = db.Column(db.Boolean, default=True)
    host_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    question_count = db.Column(db.Integer, default=10)
    difficulty = db.Column(db.String(10), default='Medium')
    time_limit = db.Column(db.Integer, default=15)
    quiz_type = db.Column(db.String(20), default='random') # random or preset
    preset_category = db.Column(db.String(100), nullable=True) # used if quiz_type is preset
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=True)

    @staticmethod
    def generate_code():
        active_count = Room.query.filter_by(is_active=True).count()
        if active_count >= 10000:
            return None # Server is full, all codes are in use
        while True:
            code = f"{random.randint(0, 9999):04d}"
            if not Room.query.filter_by(room_code=code, is_active=True).first():
                return code



class RoomPlayer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)

class PlayerStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    score = db.Column(db.Integer)
    correct_answers = db.Column(db.Integer)

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_published = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to easily access questions
    questions = db.relationship('Question', backref='quiz', lazy=True, cascade="all, delete-orphan")

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=True)
    category = db.Column(db.String(100), nullable=True) # used for preset quizzes (filtering questions by category)
    text = db.Column(db.String(500), nullable=False)
    correct_answer = db.Column(db.String(10), nullable=False)
    question_type = db.Column(db.String(20), default="multiple_choice")
    choices = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
