"""adds submission id to pairings

Revision ID: 1498d3a2a6b9
Revises: b0a75081ac85
Create Date: 2018-04-06 05:40:32.780145

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1498d3a2a6b9'
down_revision = 'b0a75081ac85'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('pairing', sa.Column('submission_id', sa.Integer(), nullable=True))
    op.drop_column('pairing', 'course_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('pairing', sa.Column('course_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_column('pairing', 'submission_id')
    # ### end Alembic commands ###