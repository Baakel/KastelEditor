from editorapp import db, app
from flask_login import LoginManager, UserMixin

lm = LoginManager(app)

wprojects = db.Table('wprojects',
                     db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
                     db.Column('project_id', db.Integer, db.ForeignKey('projects.id')))


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    oaccess_token = db.Column(db.String(64), unique=True)
    nickname = db.Column(db.String(64), index=True, unique=True)
    contact = db.Column(db.String(64), index=True, unique=True)
    wprojects = db.relationship('Projects',
                                secondary=wprojects,
                                primaryjoin=(wprojects.c.user_id == id),
                                secondaryjoin=(wprojects.c.project_id == id),
                                backref=db.backref('editors', lazy='dynamic'),
                                lazy='dynamic')

    def contribute(self, project):
        if not self.is_contributing(project):
            self.wprojects.append(project)
            return self

    def revoke_access(self, project):
        if self.is_contributing(project):
            self.wprojects.remove(project)
            return self

    def is_contributing(self, project):
        return self.wprojects.filter(wprojects.c.project_id == project.id).count() > 0

class Stakeholder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(64), index=True, unique=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))


class Good(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(140))
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))


class SoftGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(140))
    priority = db.Column(db.Boolean(), default=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))


class Projects(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    hard_goals = db.Column(db.String(140))
    soft_goals = db.relationship('SoftGoal', backref='project', lazy='dynamic')
    stake_holders= db.relationship('Stakeholder', backref='project', lazy='dynamic')
    goods = db.relationship('Good', backref='project', lazy='dynamic')


