import threading
import pytest
import os
from app import create_app
from app.extensions import db
from app.models.user import User
from werkzeug.security import generate_password_hash
from app import socketio
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from werkzeug.serving import make_server

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-secret-key"
    })

    with app.app_context():
        db.create_all()
        yield app

        db.session.rollback()
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_client(client, app):
    with app.app_context():
        user = User(username='tester', password_hash=generate_password_hash('Password123'))
        db.session.add(user)
        db.session.commit()
        
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True
            
    return client

@pytest.fixture
def socket_client(app, auth_client):
    return socketio.test_client(app, flask_test_client=auth_client)

@pytest.fixture(scope='session')
def driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless') 
    options.add_argument('--window-size=1920,1080')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    yield driver
    driver.quit()

@pytest.fixture(scope='session')
def live_server():
    app = create_app()
    db_path = os.path.join(os.getcwd(), 'selenium_test.db')
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        "SECRET_KEY": "selenium-secret-key",
        "DEBUG": False
    })

    with app.app_context():
        db.drop_all() 
        db.create_all()

        user = User(username='tester', password_hash=generate_password_hash('Password123'))
        db.session.add(user)
        db.session.commit()

    server = make_server('127.0.0.1', 5001, app)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    yield "http://127.0.0.1:5001"
    
    server.shutdown()
    if os.path.exists(db_path):
        os.remove(db_path)