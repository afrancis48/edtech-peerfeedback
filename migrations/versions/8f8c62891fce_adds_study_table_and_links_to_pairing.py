"""adds study table and links to pairing

Revision ID: 8f8c62891fce
Revises: 5c85a5b575dd
Create Date: 2019-06-30 08:09:02.378092

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8f8c62891fce'
down_revision = '5c85a5b575dd'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('study',
    sa.Column('created_on', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_on', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=150), nullable=True),
    sa.Column('start_date', sa.DateTime(), nullable=True),
    sa.Column('end_date', sa.DateTime(), nullable=True),
    sa.Column('assignments', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('pairing', sa.Column('pseudo_name', sa.String(length=150), nullable=True))
    op.add_column('pairing', sa.Column('study_id', sa.Integer(), nullable=True))
    op.create_foreign_key('pairing_study_fk', 'pairing', 'study', ['study_id'], ['id'], onupdate='CASCADE', ondelete='SET NULL')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('pairing_study_fk', 'pairing', type_='foreignkey')
    op.drop_column('pairing', 'study_id')
    op.drop_column('pairing', 'pseudo_name')
    op.drop_table('study')
    # ### end Alembic commands ###
