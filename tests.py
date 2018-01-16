import os
import unittest

from config import basedir
from editorapp import app, db
from editorapp.models import Users, Projects, wprojects


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
        u1 = Users(oaccess_token=10, nickname='john', contact='thrauglor@hotmail.com')
        u2 = Users(oaccess_token=22, nickname='lisa', contact='baakel@gmail.com')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        p1 = Projects(id=30, name='Kastel')
        p2 = Projects(id=35, name='EditorBass')
        db.session.add(p1)
        db.session.add(p2)
        db.session.commit()
        assert u1.revoke_access(p1) is None
        u_1 = u1.contribute(p1)
        db.session.add(u_1)
        db.session.commit()
        assert u1.contribute(p1) is None
        assert u1.is_contributing(p1)
        assert u1.wprojects.count() == 1
        assert u1.wprojects.first().name == 'Kastel'
        assert p1.editors.count() == 1
        assert p1.editors.first().nickname == 'john'
        assert u2.revoke_access(p1) is None
        u_2 = u2.contribute(p1)
        db.session.add(u_2)
        db.session.commit()
        assert u2.contribute(p1) is None
        assert u2.is_contributing(p1)
        assert u2.wprojects.count() == 1
        assert u2.wprojects.first().name == 'Kastel'
        assert p1.editors.count() == 2
        assert p1.editors.first().nickname == 'lisa'
        u = u1.revoke_access(p1)
        assert u is not None
        db.session.add(u)
        db.session.commit()
        assert not u1.is_contributing(p1)
        assert u1.wprojects.count() == 0
        assert p1.editors.count() == 0