from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
hard_goal = Table('hard_goal', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('authenticity', String(length=280)),
    Column('confidentiality', String(length=280)),
    Column('integrity', String(length=280)),
    Column('applications', String(length=280)),
    Column('services', String(length=280)),
    Column('priority', Boolean, default=ColumnDefault(False)),
    Column('cb_value', String(length=300)),
    Column('description', String(length=500)),
    Column('extra_hg_used', Boolean),
    Column('extra_hg', Boolean),
    Column('original_hg', Integer),
    Column('project_id', Integer),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['hard_goal'].columns['extra_hg'].create()
    post_meta.tables['hard_goal'].columns['original_hg'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['hard_goal'].columns['extra_hg'].drop()
    post_meta.tables['hard_goal'].columns['original_hg'].drop()
