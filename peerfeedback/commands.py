# -*- coding: utf-8 -*-
"""Click commands."""
import csv
import logging
import os
import random
import sys
from datetime import datetime
from glob import glob
from re import T
from subprocess import call

import click
import requests
from canvasapi import Canvas
from faker import Faker
from flask import current_app
from flask.cli import with_appcontext
from rq import get_current_job
from werkzeug.exceptions import MethodNotAllowed, NotFound
from yaml import safe_load

from peerfeedback.api import errors
from peerfeedback.api.jobs.sendmail import send_pairing_email
from peerfeedback.api.utils import (
    create_pairing,
    generate_non_group_pairs,
    get_canvas_client,
    get_db_users,
)
from peerfeedback.database import db
from peerfeedback.extensions import rq
from peerfeedback.models import AssignmentSettings, Rubric, RubricCriteria, Study, User
from peerfeedback.utils import update_canvas_token

HERE = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.join(HERE, os.pardir)
TEST_PATH = os.path.join(PROJECT_ROOT, "tests")

fake = Faker()
logger = logging.getLogger(__name__)


@click.command()
def test():
    """Run the tests."""
    import pytest

    rv = pytest.main([TEST_PATH, "--verbose"])
    exit(rv)


@click.command()
@click.option(
    "-f",
    "--fix-imports",
    default=False,
    is_flag=True,
    help="Fix imports using isort, before linting",
)
def lint(fix_imports):
    """Lint and check code style with flake8 and isort."""
    root_files = glob("*.py")
    root_directories = ["peerfeedback", "tests"]
    files_and_directories = root_files + root_directories

    def execute_tool(description, *args):
        """Execute a checking tool with its arguments."""
        command_line = list(args) + files_and_directories
        click.echo("{}: {}".format(description, " ".join(command_line)))
        rv = call(command_line)
        if rv != 0:
            exit(rv)

    if fix_imports:
        execute_tool("Fixing import order", "isort", "-rc")
    execute_tool("Linting with Black", "black")


@click.command()
def clean():
    """Remove *.pyc and *.pyo files recursively starting at current directory.

    Borrowed from Flask-Script, converted to use Click.
    """
    for dirpath, dirnames, filenames in os.walk("."):
        for filename in filenames:
            if filename.endswith(".pyc") or filename.endswith(".pyo"):
                full_pathname = os.path.join(dirpath, filename)
                click.echo("Removing {}".format(full_pathname))
                os.remove(full_pathname)


@click.command()
@click.option("--url", default=None, help="Url to test (ex. /static/image.png)")
@click.option(
    "--order", default="rule", help="Property on Rule to order by (default: rule)"
)
@with_appcontext
def urls(url, order):
    """Display all of the url matching routes for the project.

    Borrowed from Flask-Script, converted to use Click.
    """
    rows = []
    column_length = 0
    column_headers = ("Rule", "Endpoint", "Arguments")

    if url:
        try:
            rule, arguments = current_app.url_map.bind("localhost").match(
                url, return_rule=True
            )
            rows.append((rule.rule, rule.endpoint, arguments))
            column_length = 3
        except (NotFound, MethodNotAllowed) as e:
            rows.append(("<{}>".format(e), None, None))
            column_length = 1
    else:
        rules = sorted(
            current_app.url_map.iter_rules(), key=lambda rule: getattr(rule, order)
        )
        for rule in rules:
            rows.append((rule.rule, rule.endpoint, None))
        column_length = 2

    str_template = ""
    table_width = 0

    if column_length >= 1:
        max_rule_length = max(len(r[0]) for r in rows)
        max_rule_length = max_rule_length if max_rule_length > 4 else 4
        str_template += "{:" + str(max_rule_length) + "}"
        table_width += max_rule_length

    if column_length >= 2:
        max_endpoint_length = max(len(str(r[1])) for r in rows)
        # max_endpoint_length = max(rows, key=len)
        max_endpoint_length = max_endpoint_length if max_endpoint_length > 8 else 8
        str_template += "  {:" + str(max_endpoint_length) + "}"
        table_width += 2 + max_endpoint_length

    if column_length >= 3:
        max_arguments_length = max(len(str(r[2])) for r in rows)
        max_arguments_length = max_arguments_length if max_arguments_length > 9 else 9
        str_template += "  {:" + str(max_arguments_length) + "}"
        table_width += 2 + max_arguments_length

    click.echo(str_template.format(*column_headers[:column_length]))
    click.echo("-" * table_width)

    for row in rows:
        click.echo(str_template.format(*row[:column_length]))


def create_user(account, index, user_type="student"):
    profile = {
        "mail": "{0}{1:04d}@example.edu".format(user_type, index),
        "name": "{0} {1}".format(user_type.capitalize(), index),
        "username": "{0}{1:04d}".format(user_type, index),
    }
    click.secho("{name}, {mail}, secure123".format(**profile))
    user = account.create_user(
        pseudonym={"unique_id": profile["mail"], "password": "secure123"},
        user={
            "name": profile["name"],
            "username": profile["username"],
            "email": profile["mail"],
        },
    )
    return user


@click.command()
@click.option("--token", default="canvas-docker", help="Canvas token")
@click.option("--students", default=300, help="Number of students to be generated")
@click.option("--tas", default=10, help="Number of TAs to be added")
@with_appcontext
def init_canvas(token, students, tas):
    """Create dummy data for Canvas."""
    base_url = current_app.config.get("CANVAS_API_URL")
    headers = {"Authorization": "Bearer " + token}
    canvas = Canvas(base_url, token)
    account = canvas.get_account(1)

    course_data = {
        "name": "Demo Math 101",
        "public_description": "This is demo course created for demo purposes",
        "license": "public_domain",
        "default_view": "assignments",
    }
    assignment_data = [
        {
            "name": "Addition",
            "description": "Addition of numbers. A basic math operation involving numbers. Submit online.",
            "submission_types": ["online_text_entry"],
            "published": True,
            "points_possible": 100,
            "position": 1,
        },
        {
            "name": "Subtraction",
            "description": "Subtraction of numbers. Upload the solution as a PDF document.",
            "submission_types": ["online_text_entry"],
            "published": True,
            "points_possible": 100,
            "position": 2,
        },
        {
            "name": "Multiplication",
            "description": "Multiplication of numbers. Upload the solution as a PDF file.",
            "submission_types": ["online_upload"],
            "allowed_extensions": ["pdf"],
            "published": True,
            "points_possible": 100,
            "position": 3,
        },
        {
            "name": "Division",
            "description": "Division of numbers. A group assignment to test group submissions.",
            "submission_types": ["online_text_entry"],
            "published": True,
            "points_possible": 100,
            "position": 4,
            "group_category_id": 1,
        },
    ]
    group_data = {
        "name": "Division Assignment Group",
        "auto_leader": "first",
        "create_group_count": 18,
    }
    assignments = []

    click.secho(
        "\n\tGenerating demo data in Canvas LMS", fg="black", bg="white", nl=False
    )
    click.secho(
        "\n\n\u2139 Creating the course %s" % course_data["name"],
        fg="cyan",
        bold=True,
        nl=False,
    )
    course = account.create_course(course=course_data, offer=True, enroll_me=True)
    click.secho("  \u2714", fg="green")

    group = course.create_group_category(**group_data)
    assignment_data[3]["group_category_id"] = group.id

    click.secho("\n\u2139 Adding assignments to the course", fg="cyan", bold=True)
    for adata in assignment_data:
        click.echo("Adding assignment {name}".format(**adata), nl=False)
        assignment = course.create_assignment(assignment=adata)
        assignments.append(assignment)
        click.secho("  \u2714", fg="green")

    click.secho("\n\u2139 Adding students to the course", fg="cyan", bold=True)

    for i in range(students):
        user = create_user(account, i)
        course.enroll_user(
            user, "StudentEnrollment", enrollment={"enrollment_state": "active"}
        )
        sub = {
            "submission": {
                "submission_type": "online_text_entry",
                "body": fake.paragraph(nb_sentences=10),
            }
        }

        api_url = base_url + "courses/{0}/assignments/{1}/submissions".format(
            course.id, assignments[0].id
        )
        url = api_url + "?as_user_id={0}".format(user.id)
        requests.post(url, json=sub, headers=headers)

        api_url = base_url + "courses/{0}/assignments/{1}/submissions".format(
            course.id, assignments[1].id
        )
        url = api_url + "?as_user_id={0}".format(user.id)
        if random.randint(0, 1):
            requests.post(url, json=sub, headers=headers)

        api_url = base_url + "courses/{0}/assignments/{1}/submissions".format(
            course.id, assignments[3].id
        )
        url = api_url + "?as_user_id={0}".format(user.id)
        requests.post(url, json=sub, headers=headers)

    click.secho(
        "\n\u2139 Creating groups for assignment: Division", fg="cyan", bold=True
    )
    response = group.assign_members()
    click.echo(response)

    click.secho("\n\u2139 Adding TAs to the course", fg="cyan", bold=True)

    for i in range(tas):
        user = create_user(account, i, user_type="ta")
        course.enroll_user(
            user, "TaEnrollment", enrollment={"enrollment_state": "active"}
        )

    click.secho("\nDONE", bg="green", fg="black", nl=False)
    click.secho(" Your Canvas LMS is populated with sample data for demo ", fg="green")
    click.secho("")


@click.command()
@with_appcontext
def add_admin():
    """Adds an admin user"""
    admin = User.query.filter_by(username="admin").first()
    if admin:
        click.secho("Admin user already exists.", fg="red")
        for k, v in admin.as_dict().items():
            click.secho("{0}: {1}".format(k, v), fg="yellow")
        return

    # Check for gabriel's email
    gabriel = User.query.filter_by(email="gabrieljoel@gmail.com").first()
    if gabriel:
        click.secho(
            "Gabriel's account already exists. Setting username to admin", fg="yellow"
        )
        gabriel.username = "admin"
        gabriel.save()
        return

    admin = User.create(
        canvas_id=0,
        email="gabrieljoel@gmail.com",
        username="admin",
        name="Admin User",
        real_name="Gabriel",
    )
    admin.save()
    click.secho("Admin user created", fg="green")


@click.command()
@with_appcontext
def add_rubric():
    """Adds a big test rubric to the database for easier testing."""
    levels_1 = [
        dict(position=0, text="clear & succinct", points=5),
        dict(position=1, text="good, need some clarification", points=4),
        dict(position=2, text="satisfactory", points=3),
        dict(position=3, text="confusing", points=2),
        dict(position=4, text="missing", points=1),
    ]
    levels_2 = [
        dict(position=0, text="clear, succinct & has done a lot of work", points=10),
        dict(position=1, text="good description and good effort", points=8),
        dict(position=2, text="satisfactory description & effort", points=6),
        dict(position=3, text="inadequate", points=5),
        dict(position=4, text="confusing description or little effort", points=4),
        dict(position=5, text="missing", points=3),
    ]
    levels_3 = [
        dict(position=0, text="perfect", points=5),
        dict(position=1, text="a few seconds over", points=4),
        dict(position=2, text="over by ten seconds or more", points=3),
    ]
    levels_4 = [
        dict(position=0, text="perfect", points=5),
        dict(position=1, text="good", points=4),
        dict(position=2, text="OK", points=3),
    ]
    criterias = [
        {
            "name": "Motivation/Introduction [10%]",
            "description": "What is the problem (no jargon)?",
            "levels": levels_1,
        },
        {
            "name": "Motivation/Introduction [10%]",
            "description": "What is it important and why should we care?",
            "levels": levels_1,
        },
        {
            "name": "Approaches (algorithm and interactive visualization) [20%]",
            "description": "What are they?",
            "levels": levels_1,
        },
        {
            "name": "Approaches (algorithm and interactive visualization) [20%]",
            "description": "How do they work?",
            "levels": levels_1,
        },
        {
            "name": "Approaches (algorithm and interactive visualization) [20%]",
            "description": "Why can they effectively solve the problem?",
            "levels": levels_1,
        },
        {
            "name": "Approaches (algorithm and interactive visualization) [20%]",
            "description": "What is new in the approaches?",
            "levels": levels_1,
        },
        {
            "name": "Data [10%]",
            "description": "How did you get it?",
            "levels": levels_1,
        },
        {
            "name": "Data [10%]",
            "description": "What are its characteristics?",
            "levels": levels_1,
        },
        {
            "name": "Experiments (approaches) [5%]",
            "description": "How did you evaluate your approaches?",
            "levels": levels_1,
        },
        {
            "name": "Experiments (results) [20%]",
            "description": "What are the results?",
            "levels": levels_2,
        },
        {
            "name": "Experiments (results) [20%]",
            "description": "How do your methods compare to other methods?",
            "levels": levels_2,
        },
        {
            "name": "Presentation delivery (timing) [5%]",
            "description": "Finished on time?",
            "levels": levels_3,
        },
        {
            "name": "Presentation delivery (speaking) [5%]",
            "description": "Spoke clearly at a good speed?",
            "levels": levels_3,
        },
        {
            "name": "Poster Design [25%]",
            "description": "Layout/Organization",
            "levels": levels_4,
        },
        {
            "name": "Poster Design [25%]",
            "description": "Text (succinct or verbose?)",
            "levels": levels_4,
        },
        {
            "name": "Poster Design [25%]",
            "description": "Graphics (relevant & appealing?)",
            "levels": levels_4,
        },
        {
            "name": "Poster Design [25%]",
            "description": "Legibility (anything too small?)",
            "levels": levels_4,
        },
        {
            "name": "Poster Design [25%]",
            "description": "Grammar & spelling",
            "levels": levels_4,
        },
    ]

    click.secho("\n\u2139 Adding Test Rubric to the database", fg="cyan", bold=True)
    rubric = Rubric.create(
        name="Test Rubric",
        description="Rubric auto generated for testing.",
        public=True,
        active=True,
    )
    rubric.save()

    rcs = []
    for c in criterias:
        rc = RubricCriteria.create(
            name=c["name"],
            description=c["description"],
            levels=c["levels"],
            rubric_id=rubric.id,
        )
        rcs.append(rc)
    db.session.add_all(rcs)
    db.session.commit()
    click.secho("\nDONE", bg="green", fg="black", nl=False)
    click.echo("\n")


@click.command("setup-study")
@click.option(
    "-f",
    "--file",
    help="YAML file containing the setup information."
    "See example at peerfeedback/resources/study.sample.yaml",
)
@with_appcontext
def setup_study(file):
    with open(file, "r") as f:
        data = safe_load(f)
    usernames = data["students"]
    assignment_ids = data["assignments"]
    study_id = data["study"]
    click.secho("\n\n\u2139 Getting study", fg="cyan", bold=True)
    study = Study.query.get(study_id)
    if not study:
        click.secho(f"\nNo study in database with ID {study_id}", fg="red")
        return

    click.secho(
        f"\n\n\u2139 Enrolling students to study: {study.name}", fg="cyan", bold=True
    )
    for username in usernames:
        user = User.query.filter_by(username=username).first()
        if not user:
            click.secho(f"\nCan't find student with username: {username}", fg="yellow")
            continue
        study.participants.append(user)
        click.secho(f"{user.name} ({username}) added as study participant")

    click.secho(f"\n\n\u2139 Enabling Assignments: {study.name}", fg="cyan", bold=True)
    study.assignments = ",".join(map(str, assignment_ids))

    db.session.add(study)
    db.session.commit()

    click.secho("\nDONE", bg="green", fg="black", nl=False)
    click.secho(f" {study.name} has been setup", fg="green")
    click.secho("")


@click.command()
@click.option("-uid", "--userid", help="User id", type=int)
@click.option("-cid", "--courseid", help="Course id", type=int)
@click.option("-aid", "--assignmentid", help="Assignment id", type=int)
@click.option("-gaid", "--groupassignmentid", help="Group assignment id", type=int)
@click.option("-rr", "--reviewrounds", default=1, help="Review rounds", type=int)
@click.option(
    "-exd", "--excludedefaulters", default=0, help="Exclude defaulters", type=int
)
@click.option(
    "-exs",
    "--excludedstudents",
    default="",
    help="Excluded students, comman separated list",
    type=str,
)
@click.option(
    "-randomsubs", default=False, help="Whether to use random submissions", type=bool
)
@click.option("-pair", default=False, help="Whether to carry out pairings", type=bool)
@with_appcontext
def preview_pairing(
    userid,
    courseid,
    assignmentid,
    groupassignmentid,
    reviewrounds,
    excludedefaulters,
    excludedstudents,
    randomsubs,
    pair,
):
    if not userid:
        click.secho(f"\nUser ID required", fg="red")
        click.secho("")
        return

    if not courseid:
        click.secho(f"\nCourse ID required", fg="red")
        click.secho("")
        return

    if not assignmentid:
        click.secho(f"\nAssignment ID required", fg="red")
        click.secho("")
        return

    user = User.query.get(userid)
    update_canvas_token(user)

    canvas = get_canvas_client(user.canvas_access_token)
    course = canvas.get_course(courseid)
    assignment = course.get_assignment(assignmentid)
    groupassignment = course.get_assignment(groupassignmentid)
    settings = AssignmentSettings.query.filter(
        AssignmentSettings.assignment_id == assignmentid
    ).first()

    all_students = course.get_users(
        include=["email"], enrollment_type=["student"], enrollment_state=["active"]
    )

    submissions = assignment.get_submissions()
    grader_canvas_ids = [sub.user_id for sub in submissions]
    submitter_canvas_ids = [
        submission.user_id
        for submission in submissions
        if submission.workflow_state != "unsubmitted"
        and not (
            submission.workflow_state == "graded"
            and submission.score
            and int(submission.score) == 0
        )
    ]

    # Randomly choosing 95% of students as a submitter
    if not submitter_canvas_ids or randomsubs:
        student_canvas_ids = [student.id for student in all_students]
        random_students = int((95 * len(student_canvas_ids)) / 100)
        submitter_canvas_ids = random.sample(student_canvas_ids, random_students)

    if excludedefaulters:
        logger.debug("Excluding defaulters. Graders are now same as submitters.")
        grader_canvas_ids = submitter_canvas_ids

    all_users = get_db_users(all_students, True)
    usermap = dict((u.id, u) for u in all_users)
    username_map = [{u.id: [u.name]} for u in all_users]
    username_mapped = dict((key, d[key]) for d in username_map for key in d)
    graders = [
        u.id
        for u in all_users
        if u.canvas_id in grader_canvas_ids and str(u.id) not in excludedstudents
    ]
    recipients = [
        u.id
        for u in all_users
        if u.canvas_id in submitter_canvas_ids and str(u.id) not in excludedstudents
    ]
    group_map = {}
    if groupassignment.group_category_id:
        # prepare a dictionary of group id with the graders
        group_category = canvas.get_group_category(groupassignment.group_category_id)
        groups = group_category.get_groups()

        # if assignment has setup as a intra_group_review
        if settings.intra_group_review:
            matchings = []
            for group in groups:
                users = group.get_users()
                group_members = get_db_users(users, False)
                group_ids = [[m.id, m.name] for m in group_members]

                for grader in group_ids:
                    matching = (
                        group.id,
                        grader[1],
                        [r[1] for r in group_ids if r[0] != grader[0]],
                    )
                    matchings.append(matching)

            pairing_rows = [
                [
                    "Grader",
                    "Recipient",
                    "Grader Group ID",
                    "Recipient Team Group ID",
                    "Teams Equal?",
                ]
            ]
            for group_id, grader, recipients in matchings:
                for recipient in recipients:
                    grader = grader
                    recipient = recipient
                    grader_groupID = group_id
                    recipient_groupID = group_id
                    is_team_equal = 1 if grader_groupID == recipient_groupID else 0
                    pairing_rows.append(
                        [
                            grader,
                            recipient,
                            grader_groupID,
                            recipient_groupID,
                            is_team_equal,
                        ]
                    )

        else:
            for group in groups:
                users = group.get_users()
                group_members = get_db_users(users, False)
                group_map[group.id] = [u.id for u in group_members if u.id in graders]
                for u in group_map[group.id]:
                    username_mapped[u].append(group.id)

            # GENERATE PAIRING

            _pairs = generate_non_group_pairs(group_map, recipients, reviewrounds)
            matchings = _pairs.items()

            pairing_rows = [
                [
                    "Grader",
                    "Recipient",
                    "Grader Group ID",
                    "Recipient Team Group ID",
                    "Teams Equal?",
                ]
            ]
            for grader_id, recipient_ids in matchings:
                for recipient_id in recipient_ids:
                    grader = username_mapped[grader_id][0]
                    recipient = username_mapped[recipient_id][0]
                    grader_groupID = username_mapped[grader_id][1]
                    recipient_groupID = username_mapped[recipient_id][1]
                    is_team_equal = 1 if grader_groupID == recipient_groupID else 0

                    pairing_rows.append(
                        [
                            grader,
                            recipient,
                            grader_groupID,
                            recipient_groupID,
                            is_team_equal,
                        ]
                    )

            if pair:
                for grader_id, recipient_ids in matchings:
                    logger.debug("Creating pairs for Grader: %d", grader_id)
                    grader = usermap[grader_id]
                    for recipient_id in recipient_ids:
                        recipient = usermap[recipient_id]

                        submission = next(
                            (
                                s
                                for s in submissions
                                if s.user_id == recipient.canvas_id
                            ),
                            None,
                        )
                        if not submission:
                            continue

                        try:
                            pair = create_pairing(
                                user,
                                grader,
                                recipient,
                                course,
                                assignment,
                            )

                            send_pairing_email.queue(pair.id)
                        except (errors.PairingToSelf, errors.PairingExists):
                            logger.warning(
                                "Grader %d and Recipient %d are already paired",
                                grader_id,
                                recipient_id,
                            )

    else:
        click.secho(
            "Cannot generate Group based pairs. Groups empty.",
            bg="red",
            fg="black",
            nl=True,
        )
        return

    # PRINT GENERATED PREVIEW PAIRING ON CONSOLE

    click.secho("\nPREVIEW PAIRING", bg="green", fg="black", nl=False)

    writer = csv.writer(sys.stdout)
    writer.writerows(pairing_rows)

    click.secho("\nDONE", bg="green", fg="black", nl=False)
    click.secho("")
