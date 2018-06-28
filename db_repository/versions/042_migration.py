from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
bb_assumptions = Table('bb_assumptions', pre_meta,
    Column('bb_id', INTEGER),
    Column('assumptions_id', INTEGER),
)

sub_service = Table('sub_service', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('name', String(length=80)),
    Column('project_id', Integer),
)

assumptions = Table('assumptions', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('name', String(length=120)),
    Column('project_id', Integer),
    Column('bbm_id', Integer),
    Column('hg_id', Integer),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['bb_assumptions'].drop()
    post_meta.tables['sub_service'].columns['project_id'].create()
    post_meta.tables['assumptions'].columns['bbm_id'].create()
    post_meta.tables['assumptions'].columns['hg_id'].create()
    post_meta.tables['assumptions'].columns['project_id'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['bb_assumptions'].create()
    post_meta.tables['sub_service'].columns['project_id'].drop()
    post_meta.tables['assumptions'].columns['bbm_id'].drop()
    post_meta.tables['assumptions'].columns['hg_id'].drop()
    post_meta.tables['assumptions'].columns['project_id'].drop()
