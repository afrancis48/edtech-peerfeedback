"""adds review task model

Revision ID: d5ff5c719c0b
Revises: e1f49ada42b7
Create Date: 2018-04-12 17:00:22.647493

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd5ff5c719c0b'
down_revision = 'e1f49ada42b7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('review_task',
    sa.Column('created_on', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_on', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=10), nullable=True),
    sa.Column('course_name', sa.String(length=150), nullable=True),
    sa.Column('assignment_name', sa.String(length=150), nullable=True),
    sa.Column('due_date', sa.DateTime(), nullable=True),
    sa.Column('done_date', sa.DateTime(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('pairing_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['pairing_id'], ['pairing.id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('task')
    op.add_column('pairing', sa.Column('course_id', sa.Integer(), nullable=True))
    op.drop_column('pairing', 'submission_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('pairing', sa.Column('submission_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_column('pairing', 'course_id')
    op.create_table('task',
    sa.Column('created_on', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('updated_on', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('type', sa.VARCHAR(length=15), autoincrement=False, nullable=True),
    sa.Column('status', sa.VARCHAR(length=10), autoincrement=False, nullable=True),
    sa.Column('due_date', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('done_date', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('owner_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('action_item_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('action_item_type', sa.VARCHAR(length=30), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], name='task_owner_id_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='task_pkey')
    )
    op.drop_table('review_task')
    # ### end Alembic commands ###