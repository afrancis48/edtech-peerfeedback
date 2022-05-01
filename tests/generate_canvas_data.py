import sys
import json
import os.path

from canvasapi import Canvas

peer_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, peer_path)

from peerfeedback.settings import DevConfig


def generate_files():
    canvas = Canvas(DevConfig.CANVAS_API_URL, "canvas-docker")
    current_dir = os.path.dirname(os.path.realpath(__file__))
    data_dir = os.path.join(current_dir, "data")
    courses = canvas.get_courses(include=["term"])

    courses_file = os.path.join(data_dir, "courses.json")
    with open(courses_file, "w") as cfile:
        cfile.write(json.dumps([c.attributes for c in courses], indent=4))

    course = canvas.get_course(courses[0].id)
    course_file = os.path.join(data_dir, "course.json")
    with open(course_file, "w") as cfile:
        cfile.write(json.dumps(course.attributes, indent=4))

    assignments = course.get_assignments()
    assignments_file = os.path.join(data_dir, "assignments.json")
    with open(assignments_file, "w") as afile:
        afile.write(json.dumps([a.attributes for a in assignments], indent=4))

    assignment = course.get_assignment(assignments[0].id)
    assignment_file = os.path.join(data_dir, "assignment.json")
    with open(assignment_file, "w") as afile:
        afile.write(json.dumps(assignment.attributes, indent=4))

    submissions = assignment.get_submissions()
    submissions_file = os.path.join(data_dir, "submissions.json")
    with open(submissions_file, "w") as sfile:
        sfile.write(json.dumps([s.attributes for s in submissions], indent=4))

    users = course.get_users(include=["enrollments"])
    users_file = os.path.join(data_dir, "users.json")
    with open(users_file, "w") as ufile:
        ufile.write(json.dumps([u.attributes for u in users], indent=4))

    teacher_enrollments = course.get_enrollments(user_id=1)
    teacher_enrollment_file = os.path.join(data_dir, "teacher_enrollments.json")
    with open(teacher_enrollment_file, "w") as tfile:
        tfile.write(json.dumps([t.attributes for t in teacher_enrollments], indent=4))

    course_users = course.get_users(include=["enrollments"])
    course_users_file = os.path.join(data_dir, "course_users.json")
    with open(course_users_file, "w") as cufile:
        cufile.write(json.dumps([c.attributes for c in course_users], indent=4))


if __name__ == "__main__":
    generate_files()
