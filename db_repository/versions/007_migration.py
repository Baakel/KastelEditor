from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
projects = Table('projects', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('name', String(length=64)),
    Column('hard_goals', String(length=140)),
)

good = Table('good', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('description', String(length=140)),
    Column('project_id', Integer),
)

stakeholder = Table('stakeholder', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('nickname', String(length=64)),
    Column('project_id', Integer),
)

soft_goal = Table('soft_goal', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('description', String(length=140)),
    Column('priority', Boolean, default=ColumnDefault(False)),
    Column('project_id', Integer),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['projects'].create()
    post_meta.tables['good'].columns['project_id'].create()
    post_meta.tables['stakeholder'].columns['project_id'].create()
    post_meta.tables['soft_goal'].columns['project_id'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['projects'].drop()
    post_meta.tables['good'].columns['project_id'].drop()
    post_meta.tables['stakeholder'].columns['project_id'].drop()
    post_meta.tables['soft_goal'].columns['project_id'].drop()
