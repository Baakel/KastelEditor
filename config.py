import os

basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
SQLALCHEMY_TRACK_MODIFICATIONS = False

WTF_CSRF_ENABLED = True
SECRET_KEY = 'memento mori'

GITHUB_CLIENT_ID = '95884482263a00b8951c'
GITHUB_CLIENT_SECRET = 'c530772373b549f9b40bfbd81ceba99f292fb211'
GITHUB_BASE_URL = 'https://api.github.com/'
GITHUB_AUTH_URL = 'https://github.com/login/oauth/'