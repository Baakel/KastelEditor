#! /usr/bin/python3
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os
from flask import Flask, request, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_github import GitHub
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'index'
github = GitHub(app)

# db = SQLAlchemy()
# migrate = Migrate()
# login = LoginManager()
# github = GitHub()
# login.login_view = 'index'
# login.login_message = 'Please login to access this page.'


# def create_app(config_class=Config):
#     app = Flask(__name__)
#     app.config.from_object(config_class)
#
#     db.init_app(app)
#     migrate.init_app(app)
#     github.init_app(app)
#     login.init_app(app)
#
#     if not app.debug and not app.testing:
#         if app.config['LOG_TO_STDOUT']:
#             stream_handler = logging.StreamHandler()
#             stream_handler.setLevel(logging.INFO)
#             app.logger.addHandler(stream_handler)
#         else:
#             if not os.path.exists('logs'):
#                 os.mkdir('logs')
#             file_handler = RotatingFileHandler('logs/kasteleditor.log',
#                                                maxBytes=10240, backupCount=10)
#             file_handler.setFormatter(logging.Formatter(
#                 '%(asctime)s %(levelname)s: %(message)s '
#                 '[in %(pathname)s:%(lineno)d]'
#             ))
#             file_handler.setLevel(logging.INFO)
#             app.logger.addHandler(file_handler)
#
#         app.logger.setLevel(logging.INFO)
#         app.logger.info('Kastel Editor Startup')
#
#     return app

if not app.debug and not app.testing:
    if app.config['LOG_TO_STDOUT']:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        app.logger.addHandler(stream_handler)
    else:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/kasteleditor.log',
                                           maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('Kastel Editor Startup')


from editorapp import views, models
# from .models import Stakeholder, Role, Users
