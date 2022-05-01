"""update assignsettings with max reviews

Revision ID: e0bdd77b83f2
Revises: 9d902449819d
Create Date: 2018-04-21 21:15:59.684020

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e0bdd77b83f2'
down_revision = '9d902449819d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('assignment_settings', sa.Column('allow_student_pairing', sa.Boolean(), nullable=True))
    op.add_column('assignment_settings', sa.Column('allow_view_peer_assignments', sa.Boolean(), nullable=True))
    op.add_column('assignment_settings', sa.Column('feedback_suggestion', sa.String(length=500), nullable=True))
    op.add_column('assignment_settings', sa.Column('max_reviews', sa.Integer(), nullable=True))
    op.drop_column('assignment_settings', 'extra_reviews')
    op.drop_column('assignment_settings', 'extra_reviews_allowed')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('assignment_settings', sa.Column('extra_reviews_allowed', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.add_column('assignment_settings', sa.Column('extra_reviews', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_column('assignment_settings', sa.Column('feedback_suggestion', sa.String(length=500), nullable=True))
    op.drop_column('assignment_settings', 'max_reviews')
    op.drop_column('assignment_settings', 'allow_student_pairing')
    op.drop_column('assignment_settings', 'allow_view_peer_assignments')
    # ### end Alembic commands ###