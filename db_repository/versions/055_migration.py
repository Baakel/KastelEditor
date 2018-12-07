from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
soft_goal = Table('soft_goal', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('cb_value', String(length=300)),
    Column('authenticity', String(length=280)),
    Column('confidentiality', String(length=280)),
    Column('integrity', String(length=280)),
    Column('priority', Boolean),
    Column('project_id', Integer),
    Column('hardgoal_id', Integer),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['soft_goal'].columns['hardgoal_id'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['soft_goal'].columns['hardgoal_id'].drop()
