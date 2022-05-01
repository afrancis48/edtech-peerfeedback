# -*- coding: utf-8 -*-
"""Defines fixtures available to all tests."""

import pytest
import json

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

from datetime import datetime, timedelta

from peerfeedback.app import create_app
from peerfeedback.database import db as _db
from peerfeedback.settings import TestConfig
from peerfeedback.models import (
    User,
    Pairing,
    Feedback,
    Task,
    Rubric,
    RubricCriteria,
    AssignmentSettings,
    ExtraFeedback,
)
from peerfeedback.models import CourseUserMap

from .mocks import start_mock_server


@pytest.fixture(scope="session", autouse=True)
def start_server():
    start_mock_server()


@pytest.fixture(scope="session")
def app():
    """An application for the tests."""
    _app = create_app(TestConfig)
    ctx = _app.test_request_context()
    ctx.push()

    yield _app

    ctx.pop()


@pytest.fixture(scope="class")
def db(app):
    """A database for the tests."""
    _db.app = app
    with app.app_context():
        _db.create_all()

    yield _db

    # Explicitly close DB connection
    _db.session.close()
    _db.drop_all()


@pytest.fixture
def client(app, db):
    return app.test_client()


@pytest.fixture(scope="class")
def users(db):
    users_data = open("tests/data/course_users.json", "r").read()
    canvas_users = json.loads(users_data)

    users = []
    for c_user in canvas_users:
        user = User.create(
            canvas_id=c_user["id"],
            username=c_user["login_id"],
            email=c_user["login_id"],
            canvas_access_token="dummy_token",
            canvas_expiration_time=datetime.now() + timedelta(days=365),
            name=c_user["name"],
            real_name=c_user["name"],
        )
        users.append(user)

    yield users

    User.query.delete()


@pytest.fixture(scope="class")
def teacher(users):
    return User.query.filter_by(email="canvas@example.edu").first()


@pytest.fixture(scope="class")
def ta(users):
    return User.query.filter_by(email="ta0000@example.edu").first()


@pytest.fixture(scope="class")
def student(users):
    return User.query.filter_by(email="student0000@example.edu").first()


@pytest.fixture
def init_assignments(db):
    assignment_data = open("tests/data/assignments.json", "r").read()
    assignments = json.loads(assignment_data)

    assignment_objs = []
    for a in assignments:
        assign = AssignmentSettings.create(
            course_id=a["course_id"], assignment_id=a["id"]
        )
        assignment_objs.append(assign)

    yield assignment_objs

    for a in assignment_objs:
        a.delete()


@pytest.fixture
def setup_coursemap(db, users):
    def create_mapping(user, utype):
        return CourseUserMap.create(user_id=user.id, role=utype, course_id=1)

    mappings = []
    for u in users:
        if "student" in u.email:
            utype = CourseUserMap.STUDENT
        elif "ta" in u.email:
            utype = CourseUserMap.TA
        else:
            utype = CourseUserMap.TEACHER
        map = create_mapping(u, utype)
        mappings.append(map)
        db.session.add(map)
    db.session.commit()

    yield mappings

    for m in mappings:
        m.delete(commit=False)
    db.session.commit()


@pytest.fixture
def pairing(db, setup_coursemap, student):
    recipient = student
    grader = User.query.filter_by(email="student0001@example.edu").first()
    pair = Pairing.create(
        type=Pairing.STUDENT,
        course_id=1,
        assignment_id=1,
        grader_id=grader.id,
        recipient_id=recipient.id,
        creator_id=grader.id,
    )

    yield pair

    pair.delete()


@pytest.fixture
def pairings(db, users):
    students = [u for u in users if "student" in u.email]
    pairs = []
    for i in range(len(students)):
        grader = students[i]
        recipient = students[i - 1]
        pair = Pairing.create(
            type=Pairing.STUDENT,
            course_id=1,
            assignment_id=1,
            grader_id=grader.id,
            recipient_id=recipient.id,
            creator_id=grader.id,
        )
        pairs.append(pair)

    yield pairs

    for p in pairs:
        p.delete(commit=False)
    db.session.commit()


@pytest.fixture
def task(pairing):
    task = Task.create(
        status=Task.COMPLETE,
        course_id=1,
        assignment_id=1,
        user_id=pairing.grader_id,
        pairing_id=pairing.id,
    )
    yield task
    task.delete()


@pytest.fixture
def paired_students(db, pairing):
    return (pairing.grader, pairing.recipient)


@pytest.fixture
def pair_ta(db, student, teacher, ta):
    pair = Pairing.create(
        type=Pairing.TA,
        course_id=1,
        assignment_id=1,
        grader_id=ta.id,
        recipient_id=student.id,
        creator_id=teacher.id,
    )
    yield pair
    pair.delete()


@pytest.fixture
def ta_task(pair_ta):
    task = Task.create(
        status=Task.COMPLETE,
        course_id=1,
        assignment_id=1,
        user_id=pair_ta.grader_id,
        pairing_id=pair_ta.id,
    )
    yield task
    task.delete()


@pytest.fixture
def rubric(db, teacher, init_assignments):
    ruby = Rubric.create(
        name="Test Rubric",
        description="Rubric for testing",
        public=True,
        owner_id=teacher.id,
    )
    criteria1 = RubricCriteria.create(
        name="Criteria 1",
        description="criteria one",
        levels=[{"position": 1, "text": "hello", "points": 10}],
        rubric_id=ruby.id,
    )
    criteria2 = RubricCriteria.create(
        name="Criteria 2",
        description="criteria two",
        levels=[{"position": 2, "text": "hello", "points": 4}],
        rubric_id=ruby.id,
    )

    for settings in init_assignments:
        settings.rubric_id = ruby.id
        settings.save()

    yield ruby

    criteria1.delete()
    criteria2.delete()
    ruby.delete()


@pytest.fixture
def feedback(db, pairing, pair_ta):
    fb = Feedback.create(
        type=Feedback.STUDENT,
        value="A test feedback fixture for testing the application",
        grades=[],
        draft=False,
        course_id=1,
        assignment_id=1,
        receiver_id=pairing.recipient.id,
        reviewer_id=pairing.grader.id,
        pairing_id=pairing.id,
    )
    fb2 = Feedback.create(
        type=Feedback.TA,
        value="A test feedback from a TA",
        grades=[],
        draft=False,
        course_id=1,
        assignment_id=1,
        receiver_id=pairing.recipient.id,
        reviewer_id=pair_ta.grader_id,
        pairing_id=pair_ta.id,
    )

    yield (fb, fb2)

    fb.delete()
    fb2.delete()


@pytest.fixture
def random_student(users):
    user = User.query.get(10)
    mapping = CourseUserMap.create(user_id=user.id, course_id=1, role="student")
    yield user
    mapping.delete()


@pytest.fixture
def extra_requests(users):
    extras_params = [
        dict(active=True, course_id=1, assignment_id=1, user_id=10),
        dict(active=True, course_id=1, assignment_id=1, user_id=11),
    ]
    for p in extras_params:
        ExtraFeedback.create(**p)

    yield

    extras = ExtraFeedback.query.all()
    for ex in extras:
        ex.delete()
