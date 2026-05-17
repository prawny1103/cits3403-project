from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, current_user
from app.models.user import User
from werkzeug.security import generate_password_hash, check_password_hash
import re 

# Flask blueprints regarding authentication, e.g. logging in, signing in, logging out

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def signup():
    # Receive the form from the client
    if (request.method == 'POST'):
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Username Validation
        # if no username entered
        if not username:
            flash('Username is required')
            return redirect(url_for('auth.signup'))

        # cap username length
        if len(username) < 3 or len(username) > 10:
            flash('Username must be between 3 and 10 characters')
            return redirect(url_for('auth.signup'))

        # no odd symbol for username
        if not re.match(r'^[A-Za-z0-9_]+$', username):
            flash('Username can only contain letters, numbers, and underscores')
            return redirect(url_for('auth.signup'))

        # password validation
        # check if password meets criteria first
        if not password:
            flash('Password is required')
            return redirect(url_for('auth.signup'))

        if len(password) < 5: 
            flash('Password has to be at least 5 characters long')
            return redirect(url_for('auth.signup'))
        
        if not re.search(r'[A-Z]', password):
            flash('Password must contain at least one uppercase letter')
            return redirect(url_for('auth.signup'))
        
        if not re.search(r'[0-9]', password):
            flash('Password must contain at least one number')
            return redirect(url_for('auth.signup'))

        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('auth.signup'))

        if (User.query.filter_by(username=username).first()):
            flash('Username already exists')
            return redirect(url_for('auth.signup')) 

        new_user = User(
            username=username, # Username stored as plaintext
            password_hash=generate_password_hash(password) # Generate salted hashed password
        )

        from app.extensions import db
        db.session.add(new_user)
        db.session.commit()

        # Automatically login after signup is successful
        login_user(new_user)
        return redirect(url_for('main.home'))

    return render_template('signup.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # If the user is logged in
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    # Get the form from the client
    if (request.method == 'POST'):
        username = request.form.get('username')
        password = request.form.get('password')

        # Database lookup for username
        user = User.query.filter_by(username=username).first()
        # Check if password is correct
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('main.home'))
        
        flash('Invalid credentials')

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.home'))
