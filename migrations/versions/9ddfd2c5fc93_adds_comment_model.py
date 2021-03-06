"""adds comment model

Revision ID: 9ddfd2c5fc93
Revises: 70e53146706d
Create Date: 2018-05-19 17:55:13.713384

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9ddfd2c5fc93'
down_revision = '70e53146706d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('comment',
    sa.Column('created_on', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_on', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('value', sa.Text(), nullable=True),
    sa.Column('submission_id', sa.Integer(), nullable=True),
    sa.Column('commenter_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['commenter_id'], ['users.id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_constraint('pairing_grader_id_fkey', 'pairing', type_='foreignkey')
    op.drop_constraint('pairing_recipient_id_fkey', 'pairing', type_='foreignkey')
    op.create_foreign_key('pairing_grader_id_fkey', 'pairing', 'users', ['recipient_id'], ['id'], onupdate='CASCADE', ondelete='CASCADE')
    op.create_foreign_key('pairing_recipient_id_fkey', 'pairing', 'users', ['grader_id'], ['id'], onupdate='CASCADE', ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('pairing_recipient_id_fkey', 'pairing', type_='foreignkey')
    op.drop_constraint('pairing_grader_id_fkey', 'pairing', type_='foreignkey')
    op.create_foreign_key('pairing_recipient_id_fkey', 'pairing', 'users', ['recipient_id'], ['id'], onupdate='CASCADE', ondelete='SET NULL')
    op.create_foreign_key('pairing_grader_id_fkey', 'pairing', 'users', ['grader_id'], ['id'], onupdate='CASCADE', ondelete='SET NULL')
    op.drop_table('comment')
    # ### end Alembic commands ###
