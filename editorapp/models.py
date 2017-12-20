from editorapp import db


class Stakeholder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(64), index=True, unique=True)


class Good(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(140))


class SoftGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(140))
    priority = db.Column(db.Boolean(), default=False)
