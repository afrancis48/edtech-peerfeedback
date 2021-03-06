"""adds course and assignment id to commet

Revision ID: 84090d13b5fd
Revises: 9ddfd2c5fc93
Create Date: 2018-05-24 16:00:57.206574

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '84090d13b5fd'
down_revision = '9ddfd2c5fc93'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('comment', sa.Column('assignment_id', sa.Integer(), nullable=True))
    op.add_column('comment', sa.Column('course_id', sa.Integer(), nullable=True))
    op.add_column('comment', sa.Column('recipient_id', sa.Integer(), nullable=True))
    op.create_foreign_key('comment_recipient_id_fk', 'comment', 'users', ['recipient_id'], ['id'], onupdate='CASCADE', ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('comment_recipient_id_fk', 'comment', type_='foreignkey')
    op.drop_column('comment', 'recipient_id')
    op.drop_column('comment', 'course_id')
    op.drop_column('comment', 'assignment_id')
    # ### end Alembic commands ###
