from editorapp import db, app
from flask_login import LoginManager
from flask_security import RoleMixin, UserMixin

lm = LoginManager(app)

wprojects = db.Table('wprojects',
                     db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
                     db.Column('project_id', db.Integer, db.ForeignKey('projects.id')))


roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'))

)


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __str__(self):
        return self.name


class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    oaccess_token = db.Column(db.String(64), unique=True)
    nickname = db.Column(db.String(64), index=True, unique=True)
    contact = db.Column(db.String(64), index=True, unique=True)
    wprojects = db.relationship('Projects',
                                secondary=wprojects,
                                backref=db.backref('editors', lazy='dynamic'),
                                lazy='dynamic')
    roles = db.relationship('Role',
                            secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

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

    def user_register(self, role):
        self.roles.append(role)
        return self

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
    authenticity = db.Column(db.String(280))
    confidentiality = db.Column(db.String(280))
    integrity = db.Column(db.String(280))
    applications = db.Column(db.String(280))
    services = db.Column(db.String(280))
    priority = db.Column(db.Boolean(), default=False)
    cb_value = db.Column(db.String(300))
    description = db.Column(db.String(500))
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


class BbMechanisms(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True)
    authenticity = db.Column(db.Boolean, default=False)
    confidentiality = db.Column(db.Boolean, default=False)
    integrity = db.Column(db.Boolean, default=False)