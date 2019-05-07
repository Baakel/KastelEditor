from editorapp import db, app, login
from flask_login import LoginManager
from flask_security import RoleMixin, UserMixin

# lm = LoginManager(app)
@login.user_loader
def load_user(id):
    return Users.query.get(int(id))

wprojects = db.Table('wprojects',
                     db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
                     db.Column('project_id', db.Integer, db.ForeignKey('projects.id')))


roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'))

)


hard_mechanism = db.Table('hard_mechanism',
                          db.Column('hg_id', db.Integer, db.ForeignKey('hard_goal.id')),
                          db.Column('bbmech_id', db.Integer, db.ForeignKey('bb_mechanisms.id')))

bb_assumptions = db.Table('bb_assumptions',
                          db.Column('bb_id', db.Integer, db.ForeignKey('bb_mechanisms.id')),
                          db.Column('assumptions_id', db.Integer, db.ForeignKey('assumptions.id')))

freq_serv = db.Table('freq_serv',
                     db.Column('fr_id', db.Integer, db.ForeignKey('functional_requirement.id')),
                     db.Column('serv_id', db.Integer, db.ForeignKey('sub_service.id')))


good_stakeholder = db.Table('good_stakeholder',
                            db.Column('good_id', db.Integer, db.ForeignKey('good.id')),
                            db.Column('stakeholder_id', db.Integer, db.ForeignKey('stakeholder.id')))


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __str__(self):
        return '{}'.format(self.name)


class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
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

    def __repr__(self):
        return '{}'.format(self.nickname)


class Stakeholder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(64))
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))

    def __repr__(self):
        return '{}'.format(self.nickname)


class Good(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(140))
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    stakeholders = db.relationship('Stakeholder',
                                   secondary=good_stakeholder,
                                   backref=db.backref('goods', lazy='dynamic'),
                                   lazy='dynamic')

    def alrdy_used(self, sh):
        return self.stakeholders.filter(good_stakeholder.c.stakeholder_id == sh.id).count() > 0

    def add_stakeholder(self, sh):
        if not self.alrdy_used(sh):
            self.stakeholders.append(sh)
            return self

    def remove_stakeholder(self, sh):
        if self.alrdy_used(sh):
            self.stakeholders.remove(sh)
            return self

    def __repr__(self):
        return '{}'.format(self.description)


class FunctionalRequirement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(280))
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    services = db.relationship('SubService',
                               secondary=freq_serv,
                               backref=db.backref('functionalreqs', lazy='dynamic'),
                               lazy='dynamic')
    def alrdy_used(self, serv):
        return self.services.filter(freq_serv.c.serv_id == serv.id).count() > 0

    def add_serv(self, serv):
        if not self.alrdy_used(serv):
            self.services.append(serv)
            return self

    def remove_serv(self, serv):
        if self.alrdy_used(serv):
            self.services.remove(serv)
            return self

    def __repr__(self):
        return '{}'.format(self.description)


class SubService(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))

    def __repr__(self):
        return '{}'.format(self.name)


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
    extra_hg_used = db.Column(db.Boolean)
    extra_hg = db.Column(db.Boolean)
    original_hg = db.Column(db.Integer)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    soft_goals = db.relationship('SoftGoal', backref='hardgoals', lazy='dynamic')
    bbmechanisms = db.relationship('BbMechanisms',
                            secondary=hard_mechanism,
                            # primaryjoin=(hard_mechanism.c.hg_id == id),
                            # secondaryjoin=(hard_mechanism.c.bbmech_id == id),
                            backref=db.backref('hardgoals', lazy='dynamic'),
                            lazy='dynamic')

    def alrdy_used(self, bbm):
        return self.bbmechanisms.filter(hard_mechanism.c.bbmech_id == bbm.id).count() > 0

    def add_bb(self, bbm):
        if not self.alrdy_used(bbm):
            self.bbmechanisms.append(bbm)
            return self

    def remove_bb(self, bbm):
        if self.alrdy_used(bbm):
            self.bbmechanisms.remove(bbm)
            return self

    def __repr__(self):
        if self.description is not None:
            return '{}'.format(self.description)
        else:
            return '<Hard Goal Place Holder {} NOT TO BE USED OR REMOVED>'.format(self.id)


class SoftGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cb_value = db.Column(db.String(300))
    authenticity = db.Column(db.String(280))
    confidentiality = db.Column(db.String(280))
    integrity = db.Column(db.String(280))
    priority = db.Column(db.Boolean)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    hardgoal_id = db.Column(db.Integer, db.ForeignKey(HardGoal.id))


class ExtraHardGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(280))

    def __repr__(self):
        return '{}'.format(self.description)


class Projects(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    creator = db.Column(db.Integer)
    name = db.Column(db.String(64), index=True, unique=True)
    final_assumptions = db.Column(db.Boolean)
    public = db.Column(db.Boolean)
    hard_goals = db.relationship('HardGoal', backref='project', lazy='dynamic')
    functional_req = db.relationship('FunctionalRequirement', backref='project')
    stake_holders = db.relationship('Stakeholder', backref='project', lazy='dynamic')
    goods = db.relationship('Good', backref='project', lazy='dynamic')
    sub_services = db.relationship('SubService', backref='project', lazy='dynamic')
    soft_goals = db.relationship('SoftGoal', backref='project', lazy='dynamic')

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


class Assumptions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))

    def __repr__(self):
        return '{}'.format(self.name)


class BbMechanisms(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True)
    authenticity = db.Column(db.Boolean, default=False)
    confidentiality = db.Column(db.Boolean, default=False)
    integrity = db.Column(db.Boolean, default=False)
    extra_hg = db.Column(db.String(280))
    assumptions = db.relationship('Assumptions',
                                   secondary=bb_assumptions,
                                   backref=db.backref('bb_mechanisms')) #, lazy='dynamic'),
                                   # lazy='dynamic')

    def alrdy_used(self, ass):
        print(self.assumptions)
        if ass in self.assumptions:
            return True
        else:
            return False
        # return self.assumptions.filter(bb_assumptions.c.assumptions_id == ass.id).count() > 0

    def add_ass(self, ass):
        if not self.alrdy_used(ass):
            self.assumptions.append(ass)
            return self

    def remove_ass(self, ass):
        if self.alrdy_used(ass):
            self.assumptions.remove(ass)
            return self

    def __repr__(self):
        return '{}'.format(self.name)