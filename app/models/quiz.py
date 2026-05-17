from datetime import datetime
import json
import random
import string
from app.extensions import db

# Model for room
class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True) # Room id is the primary key
    room_code = db.Column(db.String(4), nullable=False) # room code is not unique, can be reused when room ends
    is_active = db.Column(db.Boolean, default=True) # Is the room currently active (game started or about to start)?
    host_id = db.Column(db.Integer, db.ForeignKey('user.id')) # User id of the user who created the room
    question_count = db.Column(db.Integer, default=10) # Number of questions (Only applicable for random quizzes where we fetch a specified amount of questions from api)
    difficulty = db.Column(db.String(10), default='Medium') # Difficulty of questions (Again, only applicable for random quizzes)
    time_limit = db.Column(db.Integer, default=15) # Time allocated to players to answer question. Quiz auto-advances if the timer runs out
    quiz_type = db.Column(db.String(20), default='random') # random or preset
    preset_category = db.Column(db.String(100), nullable=True) # used if quiz_type is preset
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=True) # id for the quiz (Only applicable for preset quizzes)

    @staticmethod
    def generate_code():
        """Generate a 4-digit room code that is not currently in use. Returns None if no room codes are available."""
        active_count = Room.query.filter_by(is_active=True).count()
        if active_count >= 10000:
            return None # Server is full, all codes are in use
        while True:
            code = f"{random.randint(0, 9999):04d}"
            if not Room.query.filter_by(room_code=code, is_active=True).first():
                return code

# Table for storing players in a room
class RoomPlayer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

# Game is used for keeping track of past games
class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)

# Table for storing results from past games
class PlayerStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    score = db.Column(db.Integer)
    correct_answers = db.Column(db.Integer)

# Table for storing custom quizzes made by users
class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_published = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to easily access questions
    questions = db.relationship('Question', backref='quiz', lazy=True, cascade="all, delete-orphan")

# Table for storing questions related to the custom quizzes made by users
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=True)
    category = db.Column(db.String(100), nullable=True) # used for preset quizzes (filtering questions by category)
    text = db.Column(db.String(500), nullable=False) # The text for the actual question, e.g. "What colour is the sky?"
    correct_answer = db.Column(db.String(10), nullable=False) # Stored as the key for an option, e.g. choice A
    question_type = db.Column(db.String(20), default="multiple_choice")
    choices = db.Column(db.Text, nullable=True) # Choices that include incorrect and correct answer
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
