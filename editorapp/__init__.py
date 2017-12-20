import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import basedir

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

from editorapp import views
from .models import Stakeholder

if Stakeholder.query.filter_by(nickname='Law').first() is None:
    law = Stakeholder(nickname='Law')
    db.session.add(law)
    db.session.commit()