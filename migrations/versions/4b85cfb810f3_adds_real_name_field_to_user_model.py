"""adds real name field to user model

Revision ID: 4b85cfb810f3
Revises: 7b6385057172
Create Date: 2018-11-14 11:33:09.713157

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4b85cfb810f3'
down_revision = '7b6385057172'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('real_name', sa.String(length=100)))
    op.execute('UPDATE users SET real_name=name')
    op.alter_column('users', 'real_name', nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'real_name')
    # ### end Alembic commands ###
