from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
migration_tmp = Table('migration_tmp', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('name', VARCHAR(length=120)),
    Column('authenticity', BOOLEAN),
    Column('confidentiality', BOOLEAN),
    Column('integrity', BOOLEAN),
    Column('extra_hg', VARCHAR(length=280)),
    Column('extra_used', BOOLEAN),
)

bb_mechanisms = Table('bb_mechanisms', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('name', String(length=120)),
    Column('authenticity', Boolean, default=ColumnDefault(False)),
    Column('confidentiality', Boolean, default=ColumnDefault(False)),
    Column('integrity', Boolean, default=ColumnDefault(False)),
    Column('extra_hg', String(length=280)),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['migration_tmp'].drop()
    post_meta.tables['bb_mechanisms'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['migration_tmp'].create()
    post_meta.tables['bb_mechanisms'].drop()
