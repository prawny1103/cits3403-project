from flask import Blueprint, render_template
from app.models import Quiz
from flask_login import login_required

# Main blueprints for url redirects

main_bp = Blueprint('main', __name__)

# The route for the landing page
@main_bp.route('/')
def home():
    return render_template('index.html')

# Route for about page (Not being used currently)
@main_bp.route('/about')
def about():
    return render_template('contactUs.html')

# Route for friends page (Not being used)
@main_bp.route('/friends')
def friends():
    return render_template('friends.html')

# Route for creating a room
@main_bp.route('/createRoom')
@login_required
def create_room():
    # Pass along all published quizzes to the render_template function so that the user can select them when creating a room
    published_quizzes = Quiz.query.filter_by(is_published=True).all()
    return render_template('createRoom.html', published_quizzes=published_quizzes)

# Route for joining a room
@main_bp.route('/joinRoom')
def join_room():
    return render_template('joinRoom.html')