"""removes rubric multi-multi relationship


Revision ID: 0f3ae846b950
Revises: 79fe18646070
Create Date: 2018-04-11 09:43:08.997892

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0f3ae846b950'
down_revision = '79fe18646070'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('rubric_map')
    op.add_column('rubric_criteria', sa.Column('rubric_id', sa.Integer(), nullable=False))
    op.create_foreign_key(None, 'rubric_criteria', 'rubric', ['rubric_id'], ['id'], onupdate='CASCADE', ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'rubric_criteria', type_='foreignkey')
    op.drop_column('rubric_criteria', 'rubric_id')
    op.create_table('rubric_map',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('rubric_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('criteria_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['criteria_id'], ['rubric_criteria.id'], name='rubric_map_criteria_id_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['rubric_id'], ['rubric.id'], name='rubric_map_rubric_id_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='rubric_map_pkey')
    )
    # ### end Alembic commands ###