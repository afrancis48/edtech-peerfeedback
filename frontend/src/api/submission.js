import axios from "axios"

export default {
  getSubmission: function({ course_id, assignment_id, user_id }, cb, errCb) {
    axios
      .get(
        `/api/course/${course_id}/assignment/${assignment_id}/user/${user_id}/`
      )
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  retryGetSubmission: function({ course_id }) {
    return axios.get(`/api/course/${course_id}/retry/`)
  }
}
