from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
hard_goal_storage = Table('hard_goal_storage', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('authenticity', BOOLEAN),
    Column('confidentiality', BOOLEAN),
    Column('integrity', BOOLEAN),
    Column('application', BOOLEAN),
    Column('service', BOOLEAN),
)

hard_goal = Table('hard_goal', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('authenticity', Boolean, default=ColumnDefault(False)),
    Column('confidentiality', Boolean, default=ColumnDefault(False)),
    Column('integrity', Boolean, default=ColumnDefault(False)),
    Column('application', Boolean, default=ColumnDefault(False)),
    Column('service', Boolean, default=ColumnDefault(False)),
    Column('project_id', Integer),
)

projects = Table('projects', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('creator', INTEGER),
    Column('name', VARCHAR(length=64)),
    Column('hard_goals', VARCHAR(length=140)),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['hard_goal_storage'].drop()
    post_meta.tables['hard_goal'].create()
    pre_meta.tables['projects'].columns['hard_goals'].drop()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['hard_goal_storage'].create()
    post_meta.tables['hard_goal'].drop()
    pre_meta.tables['projects'].columns['hard_goals'].create()
