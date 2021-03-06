"""adds tables feedback, task, draft

Revision ID: f121dec753f3
Revises: 4821a659222e
Create Date: 2018-03-18 16:32:36.557843

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f121dec753f3'
down_revision = '4821a659222e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('assignment',
    sa.Column('created_on', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_on', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('canvas_id', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('draft',
    sa.Column('created_on', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_on', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('owner', sa.Integer(), nullable=True),
    sa.Column('version', sa.Integer(), nullable=True),
    sa.Column('content', sa.Text(), nullable=True),
    sa.Column('pairing', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['owner'], ['users.id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['pairing'], ['pairing.id'], onupdate='CASCADE', ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('feedback',
    sa.Column('created_on', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_on', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('pairing', sa.Integer(), nullable=True),
    sa.Column('assignment', sa.Integer(), nullable=True),
    sa.Column('type', sa.String(length=15), nullable=True),
    sa.Column('value', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['assignment'], ['assignment.id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['pairing'], ['pairing.id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('task',
    sa.Column('created_on', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_on', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('assignee', sa.Integer(), nullable=True),
    sa.Column('type', sa.String(length=15), nullable=True),
    sa.Column('status', sa.String(length=10), nullable=True),
    sa.Column('due_date', sa.DateTime(), nullable=True),
    sa.Column('done_date', sa.DateTime(), nullable=True),
    sa.Column('pairing', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['assignee'], ['users.id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['pairing'], ['pairing.id'], onupdate='CASCADE', ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('pairing', sa.Column('assignment', sa.Integer(), nullable=False))
    op.add_column('pairing', sa.Column('grader', sa.Integer(), nullable=True))
    op.add_column('pairing', sa.Column('recipient', sa.Integer(), nullable=False))
    op.add_column('pairing', sa.Column('type', sa.String(length=10), nullable=True))
    op.create_foreign_key(None, 'pairing', 'users', ['recipient'], ['id'], onupdate='CASCADE', ondelete='SET NULL')
    op.create_foreign_key(None, 'pairing', 'users', ['grader'], ['id'], onupdate='CASCADE', ondelete='SET NULL')
    op.create_foreign_key(None, 'pairing', 'assignment', ['assignment'], ['id'], onupdate='CASCADE', ondelete='CASCADE')
    op.drop_column('pairing', 'assignment_id')
    op.drop_column('pairing', 'student_recipient')
    op.drop_column('pairing', 'student_grader')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('pairing', sa.Column('student_grader', sa.INTEGER(), autoincrement=False, nullable=False))
    op.add_column('pairing', sa.Column('student_recipient', sa.INTEGER(), autoincrement=False, nullable=False))
    op.add_column('pairing', sa.Column('assignment_id', sa.INTEGER(), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'pairing', type_='foreignkey')
    op.drop_constraint(None, 'pairing', type_='foreignkey')
    op.drop_constraint(None, 'pairing', type_='foreignkey')
    op.drop_column('pairing', 'type')
    op.drop_column('pairing', 'recipient')
    op.drop_column('pairing', 'grader')
    op.drop_column('pairing', 'assignment')
    op.drop_table('task')
    op.drop_table('feedback')
    op.drop_table('draft')
    op.drop_table('assignment')
    # ### end Alembic commands ###
