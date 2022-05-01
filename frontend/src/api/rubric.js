import axios from "axios"

export default {
  getRubrics: function(cb, errCb) {
    axios
      .get("/api/rubrics/")
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  createNewRubric: function(data, cb, errCb) {
    axios
      .post("/api/rubric/", data)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  getRubric: function(id, cb, errCb) {
    axios
      .get(`/api/rubric/${id}/`)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  getMyRubrics: function(cb, errCb) {
    axios
      .get("/api/rubrics/mine/")
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  updateRubric: function(rid, data, cb, errCb) {
    axios
      .put(`/api/rubric/${rid}/`, data)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  }
}
