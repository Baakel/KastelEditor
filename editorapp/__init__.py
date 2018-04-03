from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_github import GitHub

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
github = GitHub(app)


from editorapp import views
from .models import Stakeholder, Role, Users
