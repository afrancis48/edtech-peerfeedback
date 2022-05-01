"""adds ml automated feedback data

Revision ID: 8ff67b055b1e
Revises: a2cb6e67e929
Create Date: 2018-12-06 15:29:40.164206

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8ff67b055b1e'
down_revision = 'a2cb6e67e929'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('feedback', sa.Column('ml_rating', sa.Integer(), nullable=True))
    op.add_column('feedback', sa.Column('ml_prob', sa.Float(), nullable=True))


def downgrade():
    op.drop_column('feedback', 'ml_rating')
    op.drop_column('feedback', 'ml_prob')
