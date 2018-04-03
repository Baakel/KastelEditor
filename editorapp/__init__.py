from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_github import GitHub

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
github = GitHub(app)


from editorapp import views
from .models import Stakeholder, Role

roles = Role.query.all()
if not roles:
    user = Role(name='user', id=1)
    admin = Role(name= 'superuser', id=2)
    db.session.add(user)
    db.session.add(admin)
    db.session.commit()
