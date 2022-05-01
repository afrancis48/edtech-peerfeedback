"""adds intra_group_review flag to asetting

Revision ID: 64f90988962c
Revises: a73f14ec29ca
Create Date: 2020-07-31 10:03:46.751617

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '64f90988962c'
down_revision = 'a73f14ec29ca'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('assignment_settings', sa.Column('intra_group_review', sa.Boolean(), server_default='f', nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('assignment_settings', 'intra_group_review')
    # ### end Alembic commands ###
