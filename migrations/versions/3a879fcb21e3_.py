"""empty message

Revision ID: 3a879fcb21e3
Revises: 64f90988962c
Create Date: 2022-04-27 18:47:04.463682

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3a879fcb21e3'
down_revision = '64f90988962c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('pairing', sa.Column('view_only', sa.Boolean(), nullable=True))
    op.add_column('task', sa.Column('view_only', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('task', 'view_only')
    op.drop_column('pairing', 'view_only')
    # ### end Alembic commands ###
