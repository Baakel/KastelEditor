from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
hard_goal_storage = Table('hard_goal_storage', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('authenticity', Boolean, default=ColumnDefault(False)),
    Column('confidentiality', Boolean, default=ColumnDefault(False)),
    Column('integrity', Boolean, default=ColumnDefault(False)),
    Column('application', Boolean, default=ColumnDefault(False)),
    Column('service', Boolean, default=ColumnDefault(False)),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['hard_goal_storage'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['hard_goal_storage'].drop()
