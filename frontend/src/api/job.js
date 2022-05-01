import axios from "axios"

export default {
  getJobStatus: function(jobId) {
    return new Promise((resolve, reject) => {
      axios
        .get(`/api/job/${jobId}/`)
        .then(resp => resolve(resp.data))
        .catch(err => reject(err))
    })
  },
  cancelScheduledJob: function(jobId) {
    return new Promise((resolve, reject) => {
      axios
        .delete(`/api/jobs/scheduled/${jobId}/`)
        .then(resp => resolve(resp.data))
        .catch(err => reject(err))
    })
  },
  getScheduledJob: function(assignmentId, type, cb, errCb) {
    axios
      .get(`/api/jobs/scheduled/?assignment_id=${assignmentId}&type=${type}`)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  }
}
