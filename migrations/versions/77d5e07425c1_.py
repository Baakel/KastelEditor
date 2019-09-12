"""empty message

Revision ID: 77d5e07425c1
Revises: a7bee1d1ceff
Create Date: 2019-09-06 18:27:43.628978

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '77d5e07425c1'
down_revision = 'a7bee1d1ceff'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('hard_goal', sa.Column('unique_id', sa.String(length=200), nullable=True))
    op.create_unique_constraint(None, 'hard_goal', ['unique_id'])
    op.drop_constraint('soft_goal_ibfk_1', 'soft_goal', type_='foreignkey')
    op.drop_column('soft_goal', 'hardgoal_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('soft_goal', sa.Column('hardgoal_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True))
    op.create_foreign_key('soft_goal_ibfk_1', 'soft_goal', 'hard_goal', ['hardgoal_id'], ['id'])
    op.drop_constraint(None, 'hard_goal', type_='unique')
    op.drop_column('hard_goal', 'unique_id')
    # ### end Alembic commands ###
