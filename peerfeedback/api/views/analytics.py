from peerfeedback.api.views import api_blueprint
from peerfeedback.api.utils import allowed_roles
from peerfeedback.models import Task


@api_blueprint.route(
    "/course/<int:course_id>/assignment/<int:assignment_id>/task-status/"
)
@allowed_roles("teacher", "ta")
def get_assignment_task_status_metrics(course_id, assignment_id):
    base_query = Task.query.filter(
        Task.course_id == course_id, Task.assignment_id == assignment_id
    )
    pending = base_query.filter(Task.status == Task.PENDING).count()
    completed = base_query.filter(Task.status == Task.COMPLETE).count()
    in_progress = base_query.filter(Task.status == Task.IN_PROGRESS).count()
    archived = base_query.filter(Task.status == Task.ARCHIVED).count()

    return {
        "pending": pending,
        "completed": completed,
        "in_progress": in_progress,
        "archived": archived,
    }
