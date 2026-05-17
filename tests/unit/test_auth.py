import pytest
from app.models.user import User
from app.extensions import db
from flask_login import current_user

# Test registration with valid inputs
def test_register_success(client, app):
    response = client.post('/register', data={
        'username': 'newuser',
        'password': 'Password123',
        'confirm_password': 'Password123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'newuser' in response.data
    
    with app.app_context():
        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        assert user.username == 'newuser'

# Test registration with mismatched passwords
def test_register_passwords_dont_match(client):
    response = client.post('/register', data={
        'username': 'matchtest',
        'password': 'Password123',
        'confirm_password': 'WrongPassword123'
    }, follow_redirects=True)
    
    assert b'Passwords do not match' in response.data

# Test login with valid credentials
def test_login_success(client, app):
    # Create a user first
    from werkzeug.security import generate_password_hash
    with app.app_context():
        user = User(username='loginuser', password_hash=generate_password_hash('Secret123'))
        db.session.add(user)
        db.session.commit()

    response = client.post('/login', data={
        'username': 'loginuser',
        'password': 'Secret123'
    }, follow_redirects=True)

    assert response.status_code == 200
    # In Flask-Login, we can check the session or current_user context
    with client.session_transaction() as sess:
        assert sess.get('_user_id') is not None

# Test login with invalid credentials. Should not work
def test_login_invalid_credentials(client, app):
    response = client.post('/login', data={
        'username': 'nonexistent',
        'password': 'WrongPassword'
    }, follow_redirects=True)
    
    assert b'Invalid credentials' in response.data

# Test logout, ensure no logged in user afterwards
def test_logout(client, auth_client):
    # Use the auth_client fixture from conftest which is already logged in
    response = auth_client.get('/logout', follow_redirects=True)
    
    with auth_client.session_transaction() as sess:
        assert sess.get('_user_id') is None