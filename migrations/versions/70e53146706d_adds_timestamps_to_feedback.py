"""adds timestamps to feedback

Revision ID: 70e53146706d
Revises: 30b847d3d27d
Create Date: 2018-05-10 05:58:43.081674

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '70e53146706d'
down_revision = '30b847d3d27d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('feedback', sa.Column('end_date', sa.DateTime(), nullable=True))
    op.add_column('feedback', sa.Column('read_time', sa.Integer(), nullable=True))
    op.add_column('feedback', sa.Column('start_date', sa.DateTime(), nullable=True))
    op.add_column('feedback', sa.Column('write_time', sa.Integer(), nullable=True))
    op.add_column('task', sa.Column('start_date', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('task', 'start_date')
    op.drop_column('feedback', 'write_time')
    op.drop_column('feedback', 'start_date')
    op.drop_column('feedback', 'read_time')
    op.drop_column('feedback', 'end_date')
    # ### end Alembic commands ###