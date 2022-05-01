import axios from "axios"

export default {
  getCourseTasks: function(course_id, cb, errCb) {
    axios
      .get(`/api/task/?status=PENDING&status=INPROGRESS&course_id=${course_id}`)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  getSubmissionTask(ids, cb, errCb) {
    axios
      // eslint-disable-next-line
      .get(`/api/course/${ids.course_id}/assignment/${ids.assignment_id}/user/${ids.user_id}/task/`)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  getAllIncompleteTasks: function(cb, errCb) {
    axios
      .get("/api/task/?status=PENDING&status=INPROGRESS")
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  archiveTask: function(id, cb, errCb) {
    axios
      .put(`/api/task/${id}/`, { status: "ARCHIVED" })
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  replaceTask: function(id, cb, errCb) {
    axios
      .post(`/api/task/${id}/replace/`)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  }
}
