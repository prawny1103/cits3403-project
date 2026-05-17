import os

# Get the path for the root folder
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Get the SECRET_KEY from the environment variables (falls back to default value 'secret-key' if environment variable cannot be found)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'secret-key'
    # Get the URL for the database from environment variables, otherwise fall back to a local SQLite file at instance/quiz.db
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'quiz.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False