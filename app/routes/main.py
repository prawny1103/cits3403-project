from flask import Blueprint, render_template
from app.models import Quiz
from flask_login import login_required

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    return render_template('index.html')

@main_bp.route('/about')
def about():
    return render_template('contactUs.html')

@main_bp.route('/friends')
def friends():
    return render_template('friends.html')

@main_bp.route('/createRoom')
@login_required
def create_room():
    published_quizzes = Quiz.query.filter_by(is_published=True).all()
    return render_template('createRoom.html', published_quizzes=published_quizzes)

@main_bp.route('/joinRoom')
def join_room():
    return render_template('joinRoom.html')