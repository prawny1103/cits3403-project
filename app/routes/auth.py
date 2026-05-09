from flask import Blueprint, render_template

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register')
def signup():
    return render_template('signup.html')

@auth_bp.route('/login')
def login():
    return render_template('login.html')
