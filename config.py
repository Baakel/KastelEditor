import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config(object):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')

    WTF_CSRF_ENABLED = True
    SECRET_KEY = 'memento mori'

    GITHUB_CLIENT_ID = '95884482263a00b8951c'
    GITHUB_CLIENT_SECRET = 'c530772373b549f9b40bfbd81ceba99f292fb211'
    GITHUB_BASE_URL = 'https://api.github.com/'
    GITHUB_AUTH_URL = 'https://github.com/login/oauth/'

    # Flask-Security configurations
    SECURITY_URL_PREFIX = "/admin"
    SECURITY_PASSWORD_HASH = "pbkdf2_sha512"
    SECURITY_PASSWORD_SALT = "NLzqitLwQmHlvjTbtmwpnOCbHcenkEbdGrgVDacqFYufykBM"

    # Override Flask-Security URL's because they don't put a / at the end

    SECURITY_POST_LOGIN_VIEW = "/admin/index.html"
    SECURITY_POST_LOGOUT_VIEW = "/admin/"
    SECURITY_LOGIN_USER_TEMPLATE = "/index.html"

    SECURITY_REGISTERABLE = False
    SECURITY_SEND_REGISTER_EMAIL = False
