ASSIGNMENT_NOT_SETUP = "Assignment not setup for accepting feedback."
ASSIGNMENT_NOT_SUBMITTED = "The user has not submitted the assignment."
BOTH_EMAILS_REQUIRED = "Email for both grader and recipient are required."
BOTH_USERS_REQUIRED = "Both grader and recipient are required."
CANNOT_FIND_TEACHER = "Couldn't find the teacher for the course. Ask your course teacher to login and activate the course"
CANNOT_FIND_STUDENT_EMAIL = (
    "Cannot find the students with the given email in the course."
)
CANNOT_FIND_STUDENT = "Cannot find the students with the given IDs"
CANVAS_ERROR = "Couldn't get the requested information from Canvas."
CONTAINS_INVALID_EMAIL = "List contains an invalid email address."
COURSE_NOT_SETUP = "The course has not been setup in Peer Feedback yet."
DB_ERROR = "Database Error. Contact the application administrator."
EXTRAS_ONLY_AFTER_DUE = "Extra pairs can be created only after the assignment due date."
FEEDBACK_NOT_SUBMITTED = "You have not yet submitted your feedback."
GRADER_RECIPIENT_SAME = "Assignment grader and recipient can not be the same."
INVALID_DATA_FORMAT = "Invalid input data format"
INVALID_EMAIL = "Email of either grader or recipient is invalid."
INVALID_ID = "Invalid ID"
INVALID_PARAMETERS = "Invalid parameters"
INVALID_RUBRIC_NAME = "Invalid Rubric name"
INVALID_STATUS = "Invalid status"
INVALID_STUDENT_COUNT = "One or more students aren't members of this class."
INVALID_USER_ID = "Invalid user ID"
MISSING_PARAMS = "The request is missing some of the required parameters."
MAX_LIMIT_REACHED = "Maximum review limit reached."
NO_RUBRIC_SCORES = "No Rubric associated with the assignment to download scores"
NOT_AUTHORISED = "You are not authorised to perform this action."
NOT_ENROLLED = "You are not enrolled in this course."
NOT_PAIRED = "You are not paired with the user to give feedback."
ONLY_TEACHERS = "Only teachers of the course are allowed to perform this action."
ONLY_TEACHERS_AND_TA = (
    "Only teachers and TAs of the course are allowed to perform this action."
)
PAIRING_EXISTS = "A pairing between the two people aready exists. Check exisiting tasks and feedbacks."
REVIEWS_EXCEED_STUDENTS = "Reviews per submission exceeds available students."
TASK_NOT_FOUND = "Task with the given id couldn't be found."
SOME_IDS_NOT_IN_COURSE = (
    "Some of the GT usernames are not part of the course. Pairing cannot be done."
)
USERNAME_MISMATCH = (
    "The GT usernames of some users are different from the ones in Canvas."
    "Contact PeerFeedback administrator with the course information."
)
AUTOMATIC_PAIRING_EXISTS = (
    "Automatic pairing exists with specified course, assignment and teacher"
)


class TeacherNotFoundException(Exception):
    """Raise if teacher not found"""


class CourseNotSetup(Exception):
    """Raised when course related information is not available in coursemap"""


class PairingToSelf(Exception):
    """Raised when an attempt is made to pair user to self"""


class PairingExists(Exception):
    """Raised when two users have already been paired for an assignment"""
