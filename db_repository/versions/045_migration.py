from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
extra_hard_goal = Table('extra_hard_goal', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('description', String(length=280)),
)

assumptions = Table('assumptions', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('name', VARCHAR(length=120)),
    Column('bbm_id', INTEGER),
    Column('hg_id', INTEGER),
    Column('project_id', INTEGER),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['extra_hard_goal'].create()
    pre_meta.tables['assumptions'].columns['bbm_id'].drop()
    pre_meta.tables['assumptions'].columns['hg_id'].drop()
    pre_meta.tables['assumptions'].columns['project_id'].drop()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['extra_hard_goal'].drop()
    pre_meta.tables['assumptions'].columns['bbm_id'].create()
    pre_meta.tables['assumptions'].columns['hg_id'].create()
    pre_meta.tables['assumptions'].columns['project_id'].create()
