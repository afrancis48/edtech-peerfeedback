"""add rubric to feedback model

Revision ID: dec4fdd34e3e
Revises: 8a28b3f24741
Create Date: 2018-04-13 19:35:05.463567

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dec4fdd34e3e'
down_revision = '8a28b3f24741'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('feedback', sa.Column('rubric_id', sa.Integer(), nullable=True))
    op.create_foreign_key('feedback_rubric_relationship', 'feedback', 'rubric', ['rubric_id'], ['id'], onupdate='CASCADE', ondelete='SET NULL')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('feedback_rubric_relationship', 'feedback', type_='foreignkey')
    op.drop_column('feedback', 'rubric_id')
    # ### end Alembic commands ###
