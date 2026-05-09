from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required
from app.models.user import User
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def signup():
    if (request.method == 'POST'):
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if (User.query.filter_by(email=email).first()):
            flash('An account with this email already exists')
            return redirect(url_for('auth.signup'))

        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password, method='sha256')
        )

        from app.extensions import db
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        return redirect(url_for('main.index'))

    return render_template('signup.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if (request.method == 'POST'):
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('main.index'))
        
        flash('Invalid credentials')
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))
