import pytest
from app.models.user import User
from app.models.quiz import Room, Quiz, Question
from app.extensions import db
from werkzeug.security import generate_password_hash

# Ensure password is hashed
def test_new_user(app):
    with app.app_context():
        user = User(username='testuser', password_hash=generate_password_hash('Password123'))
        db.session.add(user)
        db.session.commit()
        
        found_user = User.query.filter_by(username='testuser').first()
        assert found_user.username == 'testuser'
        assert found_user.password_hash != 'Password123'

# Test to make sure room code is generated correctly
def test_generate_room_code(app):
    with app.app_context():
        code = Room.generate_code()
        assert len(code) == 4
        assert code.isdigit()

# Testing that Quiz and Question model relationship works
def test_quiz_question_relationship(app):
    with app.app_context():
        # Create a user first for the foreign key
        user = User(username='creator', password_hash='hash')
        db.session.add(user)
        db.session.commit()

        quiz = Quiz(title='History Quiz', creator_id=user.id)
        db.session.add(quiz)
        db.session.commit()

        question = Question(quiz_id=quiz.id, text='When was Magna Carta?', correct_answer='1215')
        db.session.add(question)
        db.session.commit()

        # Test relationship
        assert len(quiz.questions) == 1
        assert quiz.questions[0].text == 'When was Magna Carta?'

        # Test cascade delete
        db.session.delete(quiz)
        db.session.commit()
        assert Question.query.filter_by(quiz_id=quiz.id).first() is None

# Ensuring rooms are active by default
def test_room_active_status(app):
    with app.app_context():
        room = Room(room_code='1234')
        db.session.add(room)
        db.session.commit()
        
        assert room.is_active is True

# Two users should not be allowed the same username
def test_user_uniqueness(app):
    from sqlalchemy.exc import IntegrityError
    with app.app_context():
        user1 = User(username='unique', password_hash='hash1')
        db.session.add(user1)
        db.session.commit()

        user2 = User(username='unique', password_hash='hash2')
        db.session.add(user2)
        with pytest.raises(IntegrityError):
            db.session.commit()