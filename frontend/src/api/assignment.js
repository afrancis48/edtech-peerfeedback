import axios from "axios"

export default {
  getCourseAssignments: function(course_id, cb, errCb) {
    axios
      .get(`/api/course/${course_id}/assignments/`)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  getAssignment: function(ids, cb, errCb) {
    axios
      .get(`/api/course/${ids.course_id}/assignment/${ids.assignment_id}/`)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  getSettings: function({ course_id, assignment_id }, cb, errCb) {
    axios
      .get(
        `/api/assignment/settings/?course_id=${course_id}&assignment_id=${assignment_id}`
      )
      .then(res => cb(res.data))
      .catch(err => errCb(err))
  },
  updateSettings: function(settings, cb, errCb) {
    axios
      .put(`/api/assignment/settings/${settings.id}/`, settings)
      .then(res => cb(res.data))
      .catch(err => errCb(err))
  },
  getTAsWithAllotments: function(ids, cb, errCb) {
    axios
      .get(`/api/course/${ids.course_id}/assignment/${ids.assignment_id}/tas/`)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  allotTAs: function(payload, cb, errCb) {
    axios
      .post("/api/pairing/ta/", payload)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  getPeers: function(ids, cb, errCb) {
    axios
      .get(
        `/api/course/${ids.course_id}/assignment/${ids.assignment_id}/peers/`
      )
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  exportAssignmentData: function(course_id, assignment_id) {
    return axios.get(
      `/api/course/${course_id}/assignment/${assignment_id}/data/`
    )
  },
  exportAssignmentScores: function(course_id, assignment_id) {
    return axios.get(
      `/api/course/${course_id}/assignment/${assignment_id}/scores/`
    )
  },
  getRubricChangeEffect: function(settings_id, cb, errCb) {
    axios
      .get(`/api/assignment/settings/${settings_id}/rubric/affected/`)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  fetchTaskMetrics: function(params, cb, errCb) {
    axios
      .get(
        `/api/course/${params.course_id}/assignment/${
          params.assignment_id
        }/task-status/`
      )
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  exportDetailedData: function(course_id, assignment_id) {
    return axios.post(
      `/api/course/${course_id}/assignment/${assignment_id}/detailed-data/`
    )
  }
}
