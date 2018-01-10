import os
import unittest

from config import basedir
from editorapp import app, db
from editorapp.models import Users, Projects


class TestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'test.db')
        self.app = app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_contribute(self):
        u1 = Users(id=223, nickname='john', contact='blrh')
        u2 = Users(nickname='lisa', contact='balrh')
        p1 = Projects(id=1, name='Kastel')
        p2 = Projects(name='Editor')
        db.session.add(u1)
        db.session.add(u2)
        db.session.add(p1)
        db.session.add(p2)
        db.session.commit()
        assert u1.revoke_access(p1) is None
        u = u1.contribute(p1)
        db.session.add(u)
        db.session.commit()
        assert u1.contribute(p1) is None
        assert u1.is_contributing(p1)
        assert u1.wprojects.count() == 1
        assert u1.wprojects.first().name == 'Kastel'