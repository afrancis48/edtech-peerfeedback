import axios from "axios"

export default {
  getExtraFeedback: function(course_id, assignment_id, cb, errCb) {
    axios
      .get(
        `/api/extra_feedback/?course_id=${course_id}&assignment_id=${assignment_id}`
      )
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  requestExtraFeedback: function(ids, cb, errCb) {
    axios
      .post("/api/extra_feedback/", ids)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  postMetaFeedback: function(meta, cb, errCb) {
    axios
      .post("/api/feedback/meta/", meta)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  getFeedbacksForSubmission: function(ids, cb, errCb) {
    let { course_id, assignment_id, user_id } = ids
    axios
      .get(
        `/api/course/${course_id}/assignment/${assignment_id}/user/${user_id}/feedbacks/`
      )
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  getExtrasGivenCount: function({ course_id, assignment_id }, cb, errCb) {
    axios
      .get(`/api/course/${course_id}/assignment/${assignment_id}/extras_given/`)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  getMyFeedback: function(ids, cb, errCb) {
    const { course_id, assignment_id, user_id } = ids
    axios
      .get(
        `/api/course/${course_id}/assignment/${assignment_id}/user/${user_id}/feedback/mine/`
      )
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  updateFeedback: function(feedback_id, data, cb, errCb) {
    axios
      .put(`/api/feedback/${feedback_id}/`, data)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  getAllUserFeedback: function(params, cb, errCb) {
    let page = params.page || 1
    let course_id = params.course_id || 0
    let sort_by = params.sort_by || "newest"
    let url = `/api/feedback/all/?page=${page}&sort_by=${sort_by}`
    if (course_id) url += `&course=${course_id}`
    axios
      .get(url)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  deleteExtraFeedbackRequest: function(id, cb, errCb) {
    axios
      .delete(`/api/extra_feedback/${id}/`)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  getAIScore: function(value, cb, errCb) {
    axios
      .post(`/api/grade-feedback/`, { value })
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  getAllFeedbacksForSubmission: function(ids, cb, errCb) {
    let { course_id, assignment_id } = ids
    axios
      .get(`/api/course/${course_id}/assignment/${assignment_id}/feedbacks/`)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  }
}
