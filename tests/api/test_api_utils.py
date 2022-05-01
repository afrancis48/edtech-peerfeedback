import pytest
import random

from unittest.mock import Mock

from peerfeedback.api.utils import generate_review_matches
from peerfeedback.api.utils import (
    assign_students_to_tas,
    user_is_ta_or_teacher,
    create_pairing,
    generate_non_group_pairs,
    create_user,
)
from peerfeedback.models import Pairing, Feedback, Task, User, UserSettings
from peerfeedback.api import errors


class TestGenerateReviewMatches(object):
    def test_simple_case(self):
        # All users submitted
        graders = [1, 2, 3]
        recipients = [1, 2, 3]
        matches = [x for x in generate_review_matches(graders, recipients, 1)]
        assert 3 == len(matches)
        for student in matches:
            assert 1 == len(student[1])

        # Only some users submitted
        graders = [1, 2, 3]
        recipients = [2, 3]
        matches = [x for x in generate_review_matches(graders, recipients, 1)]
        assert 3 == len(matches)
        for student in matches:
            assert 1 == len(student[1])

    def test_raise_error_on_over_reviewing(self):
        """Test that the function raises an exception if the no.of reviews
        rounds required is more than available possibilities
        """

        # Rounds should be less than graders as the user cannot review his own work.
        graders = [1, 2, 3]
        recipients = [1, 2, 3]
        with pytest.raises(ValueError):
            matches = [x for x in generate_review_matches(graders, recipients, 3)]
        with pytest.raises(ValueError):
            matches = [x for x in generate_review_matches(graders, recipients, 4)]

        # Reviews rounds should be less than submissions
        graders = [1, 2, 3, 4, 5]
        recipients = [2, 3]
        with pytest.raises(ValueError):
            matches = [x for x in generate_review_matches(graders, recipients, 2)]
        with pytest.raises(ValueError):
            matches = [x for x in generate_review_matches(graders, recipients, 3)]

    def test_all_the_reviewers_are_unique(self):
        """Test to ensure that the same person is not reviewing a assignment
        twice.
        """
        # Everybody submitted
        graders = list(range(5, 15))
        recipients = list(range(5, 15))
        matches = [x for x in generate_review_matches(graders, recipients, 9)]
        assert 10 == len(matches)
        for student, peers in matches:
            # set gives the unique values
            assert len(set(peers)) == len(peers)

        # Only some submitted
        matches = [x for x in generate_review_matches(graders, recipients[:-1], 8)]
        assert 10 == len(matches)
        for student, peers in matches:
            assert len(set(peers)) == len(peers)

    def test_user_is_not_reviewing_himself(self):
        graders = list(range(100, 200))
        recipients = list(range(100, 200))
        matches = [x for x in generate_review_matches(graders, recipients, 99)]
        assert 100 == len(matches)
        for student, peers in matches:
            assert student not in peers

        graders = list(range(300, 400))
        recipients = [x for x in range(300, 400) if random.choice([True, False])]
        matches = [
            x for x in generate_review_matches(graders, recipients, len(recipients) - 1)
        ]
        assert 100 == len(matches)
        for student, peers in matches:
            assert student not in peers

    def test_everyone_has_reviews_to_give(self):
        graders = list(range(20, 30))
        recipients = list(range(20, 30))
        matches = [x for x in generate_review_matches(graders, recipients, 3)]
        for student, peers in matches:
            assert 3 == len(peers)

        recipients = [25, 28]
        matches = [x for x in generate_review_matches(graders, recipients, 1)]
        for student, peers in matches:
            assert 1 == len(peers)


class TestAssignStudentsToTAs(object):
    allotment = [{"ta_id": 99, "student_count": 4}, {"ta_id": 98, "student_count": 5}]

    def test_assignment_happens(self):
        students = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        allotted = assign_students_to_tas(self.allotment, students)

        assert all(["student_ids" in a for a in allotted])
        assert 9 == sum([len(a["student_ids"]) for a in allotted])

    def test_throws_value_error_if_students_dont_match_allotments(self):
        students = [1, 2, 3]

        with pytest.raises(ValueError):
            assign_students_to_tas(self.allotment, students)

    def test_each_allotment_is_unique(self):
        st1 = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        in1 = [{"ta_id": 98, "student_count": 4}, {"ta_id": 97, "student_count": 5}]
        allotted_1 = assign_students_to_tas(in1, st1)

        st2 = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        in2 = [{"ta_id": 98, "student_count": 4}, {"ta_id": 97, "student_count": 5}]
        allotted_2 = assign_students_to_tas(in2, st2)

        assert allotted_1[0]["ta_id"] == allotted_2[0]["ta_id"]
        assert sorted(allotted_1[0]["student_ids"]) != sorted(
            allotted_2[0]["student_ids"]
        )

    def test_the_allotments_happen_for_all_TAs(self):
        students = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        allotted = assign_students_to_tas(self.allotment, students)
        assert len(self.allotment) == len(allotted)

    def test_allotted_student_length_matches_the_expected_count(self):
        students = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        allotted = assign_students_to_tas(self.allotment, students)

        assert all(
            int(allot["student_count"]) == len(allot["student_ids"])
            for allot in allotted
        )


@pytest.mark.usefixtures("setup_coursemap")
class TestUserIsTAorTeacher(object):
    """
    FUNCTION    user_is_ta_or_teacher
    GIVEN   the course is mapped with CourseUserMap entries
    WHEN    the function is called with the course_id and user
    THEN    the function returns a boolean status
    """

    def test_returns_true_for_teacher(self, teacher):
        assert user_is_ta_or_teacher(teacher, course_id=1)

    def test_returns_true_for_ta(self, ta):
        assert user_is_ta_or_teacher(ta, course_id=1)

    def test_returns_false_for_student(self, student):
        assert not user_is_ta_or_teacher(student, course_id=1)


class TestCreatePairing(object):
    """
    FUNCTION    create_pairing
    """

    @classmethod
    def setup_class(cls):
        cls.course = Mock()
        cls.course.configure_mock(id=1, name="Test Course")
        cls.assignment = Mock()
        cls.assignment.configure_mock(
            id=1, name="Assignment 1", due_at="2018-01-01T12:00:00"
        )

    @pytest.mark.usefixtures("init_assignments")
    def test_creates_pairing_with_task_and_feedback(self, db, users, teacher):
        """
        GIVEN   the course has been setup
        WHEN    the function is called with a users who are not paired
        THEN    return a new pairing with task and feedback created
        """
        grader = users[1]
        recipient = users[2]
        assert 0 == db.session.query(Pairing).count()
        assert 0 == db.session.query(Task).count()
        assert 0 == db.session.query(Feedback).count()

        pair = create_pairing(teacher, grader, recipient, self.course, self.assignment)
        assert pair.grader_id == grader.id
        assert pair.recipient_id == recipient.id
        assert 1 == db.session.query(Pairing).count()
        assert 1 == db.session.query(Task).count()
        assert 1 == db.session.query(Feedback).count()
        # Cleanup after test
        pair.delete()

    def test_raises_error_if_assignment_settings_not_found(self, teacher, users):
        """
        GIVEN   the course is not setup
        WHEN    the function is called with params
        THEN    a CourseNotSetup error is raised
        """
        grader = users[1]
        recipient = users[2]
        with pytest.raises(errors.CourseNotSetup):
            create_pairing(teacher, grader, recipient, self.course, self.assignment)

    @pytest.mark.usefixtures("init_assignments")
    def test_raises_error_if_grader_and_recipient_are_same(self, teacher, student):
        """
        GIVEN   the course is setup
        WHEN    the function is called with same grader and recipient params
        THEN    an error is raised
        """
        with pytest.raises(errors.PairingToSelf):
            create_pairing(teacher, student, student, self.course, self.assignment)

    @pytest.mark.usefixtures("init_assignments")
    def test_raises_error_if_pairing_already_exists(self, teacher, paired_students):
        """
        GIVEN   the course is setup and a pairing already exists for an assignment
        WHEN    the function is called with the same grader and recipient
        THEN    an error is raised
        """
        grader, recipient = paired_students
        with pytest.raises(errors.PairingExists):
            create_pairing(teacher, grader, recipient, self.course, self.assignment)


class TestGenerateNonGroupPairs():
    @classmethod
    def setup_class(cls):
        cls.groups = {
            1: [1, 2, 3, 4],
            2: [6, 7, 8, 9],
            4: [10, 12, 13, 14],
            5: [18, 19],
            8: [20, 21, 22],
            17: [5, 11, 15, 16, 17]
        }
        cls.all = [i for i in range(1, 23)]
        cls.some = [1, 2, 3, 6, 7, 9, 12, 13, 14, 19, 20, 22, 11, 15, 5, 17]

    def test_everyone_has_required_number_of_pairs(self):
        rounds = 3
        pairs = generate_non_group_pairs(self.groups, self.all, rounds)
        for grader, peers in pairs.items():
            assert len(peers) == rounds

        pairs = generate_non_group_pairs(self.groups, self.some, rounds)
        for grader, peers in pairs.items():
            assert len(peers) == rounds

    def test_everyone_is_assigned_a_reviewer(self):
        recipients = []
        pairing = generate_non_group_pairs(self.groups, self.all, 1)
        for grader, peers in pairing.items():
            assert len(peers) == 1
            recipients.extend(peers)
        assert len(set(recipients)) == len(self.all)

        recipients = []
        pairing = generate_non_group_pairs(self.groups, self.some, 1)
        for grader, peers in pairing.items():
            assert len(peers) == 1
            recipients.extend(peers)
        assert len(set(recipients)) == len(self.some)

    def test_recipients_paired_to_grader_are_unique(self):
        pairing = generate_non_group_pairs(self.groups, self.all, 5)
        for peers in pairing.values():
            assert len(peers) == len(set(peers))

        pairing = generate_non_group_pairs(self.groups, self.some, 5)
        for peers in pairing.values():
            assert len(peers) == len(set(peers))

    def test_users_from_the_same_group_are_not_assigned_to_each_other(self):
        pairing = generate_non_group_pairs(self.groups, self.all, 5)
        for group, members in self.groups.items():
            for user in members:
                assert all(m not in pairing[user] for m in members)

        pairing = generate_non_group_pairs(self.groups, self.some, 5)
        for group, members in self.groups.items():
            for user in members:
                assert all(m not in pairing[user] for m in members)


class TestCreateUser(object):
    def setup(self):
        self.mock_user = Mock()
        profile = {
            "primary_email": "mockuser@example.edu",
            "login_id": "mockuser",
            "avatar_url": "https://example.com/",
            "name": "Mock User",
            "bio": "A Mock user object",
            "id": 5000
        }
        self.mock_user.id = 5000
        self.mock_user.get_profile.return_value = profile

    def teardown(self):
        User.query.delete()

    def test_adds_new_user_with_settings(self, db):
        assert len(User.query.all()) == 0
        assert len(UserSettings.query.all()) == 0

        user = create_user(self.mock_user)

        assert len(User.query.all()) == 1
        assert len(UserSettings.query.all()) == 1

    def test_settings_gets_saved_later_when_called_with_save_as_false(self, db):
        assert len(User.query.all()) == 0
        assert len(UserSettings.query.all()) == 0

        user = create_user(self.mock_user, False)
        db.session.add(user)
        db.session.commit()

        assert len(User.query.all()) == 1
        assert len(UserSettings.query.all()) == 1
