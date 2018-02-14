from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
soft_goal = Table('soft_goal', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('description', VARCHAR(length=140)),
    Column('priority', BOOLEAN),
    Column('project_id', INTEGER),
)

functional_requirement = Table('functional_requirement', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('description', String(length=280)),
    Column('project_id', Integer),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['soft_goal'].drop()
    post_meta.tables['functional_requirement'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['soft_goal'].create()
    post_meta.tables['functional_requirement'].drop()
