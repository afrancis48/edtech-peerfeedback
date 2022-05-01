"""adds avatar and bio to user

Revision ID: ecea45e28dbc
Revises: 2f4bc1bcaf32
Create Date: 2018-06-27 13:23:26.259531

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ecea45e28dbc'
down_revision = '2f4bc1bcaf32'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('avatar_url', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('bio', sa.Text(), nullable=True))
    op.drop_column('users', 'active')
    op.drop_column('users', 'is_admin')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('is_admin', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('active', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.drop_column('users', 'bio')
    op.drop_column('users', 'avatar_url')
    # ### end Alembic commands ###
