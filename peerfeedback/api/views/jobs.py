from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_current_user
from rq.registry import StartedJobRegistry

from peerfeedback.api.views import api_blueprint
from peerfeedback.extensions import rq


@api_blueprint.route("/job/<job_id>/")
@jwt_required
def job_status(job_id):
    """Returns the status of a background job with the given job id

    :param job_id: UUID of the Redis Queue job
    :return: the status of the job
    """
    queue = rq.get_queue("high")
    job = queue.fetch_job(job_id)
    if not job:
        queue = rq.get_queue("default")
        job = queue.fetch_job(job_id)

    if job.is_finished:
        return jsonify(job.result)
    elif job.is_started:
        data = {"status": "in_progress"}
        if job.meta.get("progress", 0):
            data["progress"] = job.meta["progress"]
        return jsonify(data)
    elif job.is_queued:
        return jsonify({"status": "pending"})
    elif job.is_failed:
        return jsonify({"status": "error", "message": "Job failed."})


@api_blueprint.route("/pairing/jobs/active/")
@jwt_required
def active_pairing_jobs():
    """return the active job id of the user"""
    user = get_current_user()
    queue = rq.get_queue("high")
    registry = StartedJobRegistry("high", connection=rq.connection)
    all_ids = registry.get_job_ids()
    jobs = []
    for _id in all_ids:
        j = queue.fetch_job(_id)
        if "pair_automatically" in j.description:
            if j.args[3] == user.id:
                jobs.append(
                    dict(
                        id=_id,
                        course_id=j.args[0],
                        assignment_id=j.args[1],
                        pairing="automatic",
                    )
                )
        elif "pair_using_csv" in j.description:
            if j.args[5] == user.id:
                jobs.append(
                    dict(
                        id=_id,
                        course_id=j.args[0],
                        assignment_id=j.args[1],
                        pairing="csv",
                    )
                )

    return jsonify(jobs)


@api_blueprint.route("/jobs/scheduled/<job_id>/", methods=["DELETE"])
@jwt_required
def cancel_scheduled_job(job_id):
    scheduler = rq.get_scheduler()
    scheduler.cancel(job_id)
    return "OK"


@api_blueprint.route("/jobs/scheduled/")
@jwt_required
def get_scheduled_jobs():
    assignment_id = int(request.args.get("assignment_id", 0))
    type = request.args.get("type", None)

    if not assignment_id:
        error = dict(status="error", message="Assignment ID Missing in Query")
        return jsonify(error), 400

    if not type:
        error = dict(status="error", message="Invalid job type")
        return jsonify(error), 400

    scheduler = rq.get_scheduler()
    jobs = scheduler.get_jobs(with_times=True)
    queued = {}
    for job, date in jobs:
        if (
            "pair_automatically" in job.func_name
            and assignment_id == job.args[1]
            and type == "auto"
        ):
            queued["id"] = job.id
            queued["date"] = date.isoformat() + "Z"
            queued["pairs"] = job.args[2]
        elif (
            "pair_using_csv" in job.func_name
            and assignment_id == job.args[1]
            and type == "csv"
        ):
            queued["id"] = job.id
            queued["date"] = date.isoformat() + "Z"
    return jsonify(queued)
