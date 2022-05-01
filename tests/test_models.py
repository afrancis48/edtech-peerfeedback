import pytest

from peerfeedback.models import (
    User,
    Pairing,
    Feedback,
    Task,
    Rubric,
    RubricCriteria,
    Comment,
    Study,
    UserSettings,
)


class TestFeedback(object):
    def test_object_created_with_valid_grades(self, db):
        """
        GIVEN   feedback model
        WHEN    an object is created with the right rubric and grades
        THEN    the object is added to the db
        """
        r = Rubric.create(name="Test Rubric")
        g = [{"criteria": "Test criteria", "level": 9}]
        Feedback.create(rubric_id=r.id, grades=g)
        assert 1 == len(Feedback.query.all())

    def test_error_raised_when_using_invalid_grades(self, db):
        """
        GIVEN   feedback model
        WHEN    invalid grades are used on the object
        THEN    an error is raised
        """
        r = Rubric.create(name="Test Rubric")

        with pytest.raises(AssertionError):
            Feedback.create(rubric_id=r.id, grades="")
        with pytest.raises(AssertionError):
            Feedback.create(rubric_id=r.id, grades=[""])
        with pytest.raises(AssertionError):
            Feedback.create(rubric_id=r.id, grades=[{}])
        with pytest.raises(AssertionError):
            Feedback.create(rubric_id=r.id, grades=[{"criteria": ""}])
        with pytest.raises(AssertionError):
            Feedback.create(rubric_id=r.id, grades=[{"level": ""}])
        with pytest.raises(AssertionError):
            Feedback.create(rubric_id=r.id, grades=[{"criteria": 9, "level": 10}])
        with pytest.raises(AssertionError):
            Feedback.create(
                rubric_id=r.id, grades=[{"criteria": "dummy", "level": "b"}]
            )


class TestComment(object):
    def test_empty_comments_are_not_saved(self, db):
        """
        GIVEN   comment model with validator for value
        WHEN    an empty string or a string of spaces is stored as comment
        THEN    an error is raised
        """
        with pytest.raises(AssertionError):
            Comment.create(value="")
        with pytest.raises(AssertionError):
            Comment.create(value="       ")
        with pytest.raises(AssertionError):
            Comment.create(value="  \n\r\n    ")


class TestRubricCriteria(object):
    def test_validates_levels_throws_error(self, db):
        """
        GIVEN   the RubricCriteria model
        WHEN    an object is created with the levels param badly formatted
        THEN    an error is raised
        """
        r = Rubric.create(name="Test Rubric")

        with pytest.raises(AssertionError):
            RubricCriteria.create(name="test", rubric_id=r.id, levels=[])
        with pytest.raises(AssertionError):
            RubricCriteria.create(name="test", rubric_id=r.id, levels={})
        with pytest.raises(AssertionError):
            RubricCriteria.create(name="test", rubric_id=r.id, levels=None)
        with pytest.raises(AssertionError):
            RubricCriteria.create(name="test", rubric_id=r.id, levels=[{}])
        with pytest.raises(AssertionError):
            l = [{"position": "a"}]
            RubricCriteria.create(name="test", rubric_id=r.id, levels=l)
        with pytest.raises(AssertionError):
            l = [{"position": 0, "text": "dummy"}]
            RubricCriteria.create(name="test", rubric_id=r.id, levels=l)
        with pytest.raises(AssertionError):
            l = [{"position": 0, "text": [], "points": 10}]
            RubricCriteria.create(name="test", rubric_id=r.id, levels=l)
        with pytest.raises(AssertionError):
            l = [{"position": 0, "text": "dummy", "points": ""}]
            RubricCriteria.create(name="test", rubric_id=r.id, levels=l)

    def test_criteria_is_added_when_the_levels_param_is_right(self, db):
        """
        GIVEN   the RubricCriteria model
        WHEN    an object is created with the properly formatted JSON for levels
        THEN    the data is added to the db
        """
        r = Rubric.create(name="Test Rubric")
        # integer points
        l = [{"position": 0, "text": "description", "points": 10}]
        rc = RubricCriteria.create(name="C1", rubric_id=r.id, levels=l)
        assert rc.id
        assert 1 == len(RubricCriteria.query.all())
        # decimal points
        l = [{"position": 0, "text": "description", "points": 5.75}]
        rc = RubricCriteria.create(name="C1", rubric_id=r.id, levels=l)
        assert rc.id
        assert 2 == len(RubricCriteria.query.all())


class TestPairing(object):
    def test_deleting_pairing_automatically_deletes_task_and_feedback(
        self, db, student, ta, teacher
    ):
        """
        GIVEN   a pairing object and associated task and feedback objects
        WHEN    the pairing is deleted from the database
        THEN    the associated task and feedback are also deleted automatically
        """
        assert 0 == len(Pairing.query.all())
        assert 0 == len(Feedback.query.all())
        assert 0 == len(Task.query.all())

        pair = Pairing.create(
            type=Pairing.TA,
            grader_id=ta.id,
            course_id=1,
            assignment_id=1,
            recipient_id=student.id,
            creator_id=teacher.id,
        )
        task = Task.create(user_id=ta.id, pairing_id=pair.id)
        feedback = Feedback.create(
            receiver_id=student.id, reviewer_id=ta.id, pairing_id=pair.id
        )

        assert 1 == len(Pairing.query.all())
        assert 1 == len(Feedback.query.all())
        assert 1 == len(Task.query.all())

        pair.delete(commit=True)

        assert 0 == len(Pairing.query.all())
        assert 0 == len(Feedback.query.all())
        assert 0 == len(Task.query.all())


class TestStudyUserAssociationTable(object):
    def test_users_are_mapped_to_studies(self, db):
        study = Study()
        study.name = "Test Study"

        u1 = User(1001, "user1", "user_1@example.edu", name="User 1", real_name="U1")
        u2 = User(1002, "user2", "user_2@example.edu", name="User Two", real_name="U2")

        study.participants.append(u1)
        study.participants.append(u2)

        db.session.add(study)
        db.session.commit()

        studies = Study.query.all()
        assert len(studies) == 1
        assert len(studies[0].participants) == 2

        study.delete()

    def test_studies_are_mapped_to_users(self, db):
        user = User(1001, "user", "user@example.edu", name="User", real_name="U ONE")

        assert len(Study.query.all()) == 0

        study1 = Study.create(name="Test Study 1")
        study2 = Study.create(name="Test Study 2")

        study1.participants.append(user)
        study2.participants.append(user)

        db.session.add_all([study1, study2])
        db.session.commit()

        assert len(user.studies) == 2


class TestUserSettingsModel(object):
    def test_user_settings_save_and_retrieve_objects(self, db, users):
        assert 0 == len(UserSettings.query.all())
        us = UserSettings.create(
            user_id=users[0].id,
            comment_emails=True,
            feedback_emails=True,
            discussion_emails=True,
        )
        assert 1 == len(UserSettings.query.all())
        us.delete()

    def test_user_settings_have_default_values(self, db, users):
        us = UserSettings.create(user_id=users[0].id)
        assert us.comment_emails is True
        assert us.feedback_emails is True
        assert us.discussion_emails is True
        us.delete()

    def test_deleting_user_deletes_settings(self, db):
        user = User.create(
            canvas_id=32,
            username="test_user",
            email="test@example.edu",
            name="Test User",
            real_name="Test User",
        )
        UserSettings.create(user_id=user.id)
        assert 1 == len(UserSettings.query.all())
        user.delete()
        assert 0 == len(UserSettings.query.all())

    def test_user_settings_is_orm_connected_to_user(self, db, users):
        settings = UserSettings.create(user_id=users[0].id)
        assert isinstance(settings.user, User)
