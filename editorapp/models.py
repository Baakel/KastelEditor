from editorapp import db, app
from flask_login import LoginManager

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
                                backref=db.backref('editors', lazy='dynamic'),
                                lazy='dynamic')

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        try:
            return unicode(self.id)
        except NameError:
            return str(self.id)

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
    nickname = db.Column(db.String(64))
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))


class Good(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(140))
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))


class FunctionalRequirement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(280))
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))


class HardGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    authenticity = db.Column(db.Boolean(), default=False)
    confidentiality = db.Column(db.Boolean(), default=False)
    integrity = db.Column(db.Boolean(), default=False)
    application = db.Column(db.Boolean(), default=False)
    service = db.Column(db.Boolean(), default=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))


class Projects(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    creator = db.Column(db.Integer)
    name = db.Column(db.String(64), index=True, unique=True)
    hard_goals = db.relationship('HardGoal', backref='project', lazy='dynamic')
    functional_req = db.relationship('FunctionalRequirement', backref='project', lazy='dynamic')
    stake_holders= db.relationship('Stakeholder', backref='project', lazy='dynamic')
    goods = db.relationship('Good', backref='project', lazy='dynamic')

    @staticmethod
    def make_unique_name(name):
        if Projects.query.filter_by(name=name).first() is None:
            return name
        version = 2
        while True:
            new_name = name + str(version)
            if Projects.query.filter_by(name=new_name).first() is None:
                break
            version += 1
        return new_name

    def __repr__(self):
        return '<Projects %r>' % self.name


