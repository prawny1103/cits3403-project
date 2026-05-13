from datetime import datetime
import json
import random
import string
from app.extensions import db

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_code = db.Column(db.String(4), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    host_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    question_count = db.Column(db.Integer, default=10)
    difficulty = db.Column(db.String(10))
    time_limit = db.Column(db.Integer, default=15)

    @staticmethod
    def generate_code():
        active_count = Room.query.count()
        if active_count >= 10000:
            return None # Server is full, all codes are in use
        while True:
            code = f"{random.randint(0, 9999):04d}"
            if not Room.query.filter_by(room_code=code).first():
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

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    correct_answer = db.Column(db.String(10), nullable=False)
    question_type = db.Column(db.String(20), default="multiple_choice")
    choices = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
