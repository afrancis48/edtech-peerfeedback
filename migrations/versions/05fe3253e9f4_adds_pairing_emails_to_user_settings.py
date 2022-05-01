"""adds pairing_emails to user settings

Revision ID: 05fe3253e9f4
Revises: c9ed9873b5b2
Create Date: 2019-08-21 07:25:38.583216

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '05fe3253e9f4'
down_revision = 'c9ed9873b5b2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user_settings', sa.Column('pairing_emails', sa.Boolean(), server_default='t', nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user_settings', 'pairing_emails')
    # ### end Alembic commands ###