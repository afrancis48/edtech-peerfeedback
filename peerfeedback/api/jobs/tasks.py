from datetime import timedelta

import dateutil

from peerfeedback.api.utils import get_canvas_client
from peerfeedback.extensions import rq
from peerfeedback.models import User, Task, AssignmentSettings


@rq.job("default")
def update_task_deadline(assignment_id, user_id):
    user = User.query.get(user_id)

    settings = AssignmentSettings.query.filter_by(assignment_id=assignment_id).first()
    if not settings:
        return {"status": "error", "message": "Assignment not present."}

    tasks = Task.query.filter_by(assignment_id=assignment_id).all()
    if not tasks:
        return {"status": "success", "message": "No Tasks to update"}

    canvas = get_canvas_client(user.canvas_access_token)
    course = canvas.get_course(tasks[0].course_id)
    assignment = course.get_assignment(assignment_id)
    if settings.deadline_format == "canvas" and not assignment.due_at:
        return {
            "status": "error",
            "message": "Cannot set canvas based deadline. Due date not set for assignment",
        }

    for task in tasks:
        if settings.deadline_format == "canvas":
            task.due_date = dateutil.parser.parse(assignment.due_at) + timedelta(
                days=settings.feedback_deadline
            )
        elif settings.deadline_format == "custom":
            task.due_date = settings.custom_deadline
        task.save()

    return {"status": "success", "message": "All tasks have been updated successfully"}
