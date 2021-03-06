"""adds creator_id to pairings

Revision ID: b6ef8a64e190
Revises: 3850eb9e4c2a
Create Date: 2018-03-31 16:04:44.519752

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b6ef8a64e190'
down_revision = '3850eb9e4c2a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('pairing', sa.Column('creator_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'pairing', 'users', ['creator_id'], ['id'], onupdate='CASCADE', ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'pairing', type_='foreignkey')
    op.drop_column('pairing', 'creator_id')
    # ### end Alembic commands ###
