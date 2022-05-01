import re
import requests

from threading import Thread
from http.server import BaseHTTPRequestHandler, HTTPServer


class MockServerRequestHandler(BaseHTTPRequestHandler):
    COURSES = re.compile("/api/v1/courses\?.*")
    COURSE_1 = re.compile("/api/v1/courses/\d(\?include.*)?")
    ASSIGNMENTS = re.compile("/api/v1/courses/1/assignments\?.*")
    ASSIGNMENT_1 = re.compile("/api/v1/courses/1/assignments/1$")
    SUBMISSIONS = re.compile("/api/v1/courses/1/assignments/1/submissions\?.*")
    SUBMISSION = re.compile(
        "/api/v1/courses/\d*/assignments/\d*/submissions/\d*(\?include.*)?"
    )
    TEACHER_ENROLLMENTS = re.compile("/api/v1/courses/\d/enrollments\?user_id=1.*")
    COURSE_USERS = re.compile("/api/v1/courses/\d/search_users\?include.*")

    def send_json_file(self, filename):
        self.send_response(requests.codes.ok)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()

        response_content = open("tests/data/" + filename, "r").read()
        self.wfile.write(response_content.encode("utf-8"))
        return

    def do_GET(self):
        filename = "courses.json"
        if re.search(self.SUBMISSION, self.path):
            filename = "submission.json"
        elif re.search(self.SUBMISSIONS, self.path):
            filename = "submissions.json"
        elif re.search(self.TEACHER_ENROLLMENTS, self.path):
            filename = "teacher_enrollments.json"
        elif re.search(self.COURSE_USERS, self.path):
            filename = "course_users.json"
        elif re.search(self.ASSIGNMENTS, self.path):
            filename = "assignments.json"
        elif re.search(self.ASSIGNMENT_1, self.path):
            filename = "assignment.json"
        elif re.search(self.COURSE_1, self.path):
            filename = "course.json"
        return self.send_json_file(filename)


def start_mock_server():
    mock_server = HTTPServer(("localhost", 8888), MockServerRequestHandler)
    mock_server_thread = Thread(target=mock_server.serve_forever)
    mock_server_thread.setDaemon(True)
    mock_server_thread.start()
