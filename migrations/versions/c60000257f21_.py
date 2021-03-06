"""empty message

Revision ID: c60000257f21
Revises: 4edc648f280f
Create Date: 2018-01-22 15:03:11.882858

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c60000257f21'
down_revision = '4edc648f280f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('pairing',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('student_grader', sa.Integer(), nullable=False),
    sa.Column('student_recipient', sa.Integer(), nullable=False),
    sa.Column('assignment_id', sa.Integer(), nullable=False),
    sa.Column('reviewRound', sa.Integer(), nullable=False),
    sa.Column('created_on', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_on', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),

    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('pairing')
    # ### end Alembic commands ###
