"""adds unique constraint to assignment settings

Revision ID: 5c85a5b575dd
Revises: 22144262862d
Create Date: 2019-02-26 04:30:07.175279

"""
import sqlalchemy as sa

from alembic import op
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy import func


# revision identifiers, used by Alembic.
revision = '5c85a5b575dd'
down_revision = '8ff67b055b1e'
branch_labels = None
depends_on = None


def remove_duplicates(session, cls, attr):
    attribute = getattr(cls, attr)
    duplicates = (
        session.query(attribute).group_by(attribute)
            .having(func.count(attribute) > 1).all()
    )
    n_dups = len(duplicates)
    print('{}.{}: {} duplicates found'.format(cls.__name__, attr, n_dups))
    for duplicate in duplicates:
        objs = (
            session.query(cls).filter(attribute == getattr(duplicate, attr))
                .order_by('id').all()
        )
        # Keep the one with extra pairs enabled
        to_keep = next(
            (o for o in objs if getattr(o, "allow_student_pairing")), None
        )
        # OR Keep the one with a rubric set
        if not to_keep:
            to_keep = next(
                (o for o in objs if getattr(o, "rubric_id")), None
            )
        # OR just keep the oldest one
        if not to_keep:
            to_keep = objs[0]
        for obj in objs:
            if obj.id != to_keep.id:
                print("Deleting: ", obj)
                session.delete(obj)
    session.commit()
    print('{}.{}: {} duplicates removed'.format(cls.__name__, attr, n_dups))


def upgrade():
    # Scan the DB for duplicates and remove them
    from peerfeedback.extensions import db
    from peerfeedback.models import AssignmentSettings as ASet

    # Ensure that the table exists before running the de-duplication
    # In case of fresh setup of the app, the tables might not hav been present
    # yet. So checking is essential
    inspector = Inspector.from_engine(db.engine)
    existing_tables = inspector.get_table_names()

    if ASet.__tablename__ in existing_tables:
        remove_duplicates(db.session, ASet, 'assignment_id')

    # Apply the unique constraint for the
    op.create_unique_constraint("uq_assignment_id", 'assignment_settings', ['assignment_id'])


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("uq_assignment_id", 'assignment_settings', type_='unique')
    # ### end Alembic commands ###