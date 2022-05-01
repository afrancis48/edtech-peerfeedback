import axios from "axios"

export default {
  getPairings: function(data, cb, errCb) {
    // eslint-disable-next-line
    let url = `/api/course/${data.course_id}/assignment/${data.assignment_id}/pairs/`
    if (data.hasOwnProperty("mine")) url += "mine/"
    axios
      .get(url)
      .then(response => cb(response.data))
      .catch(error => errCb(error))
  },
  createAutoPairs: function(data, cb, errCb) {
    axios
      .post("/api/pairing/automatic/", data)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  createManualPairs: function(data, cb, errCb) {
    axios
      .post("/api/pairing/manual/", data)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  createCSVPairs: function(data, cb, errCb) {
    axios
      .post("/api/pairing/csv/", data)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  createPairing: function(data, cb, errCb) {
    axios
      .post("/api/pairing/", data)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  getActiveJobs: function(cb, errCb) {
    axios
      .get("/api/pairing/jobs/active/")
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  searchPairings: function(params, cb, errCb) {
    // eslint-disable-next-line
    let url = `/api/course/${params.course_id}/assignment/${params.assignment_id}/pairs/search?`
    let queries = []
    if (params.hasOwnProperty("grader")) queries.push("grader=" + params.grader)
    if (params.hasOwnProperty("recipient"))
      queries.push("recipient=" + params.recipient)
    url += queries.join("&")

    axios
      .get(url)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  getPairingPage: function(data, cb, errCb) {
    let { course_id, assignment_id, page, per_page } = data
    let url = `/api/course/${course_id}/assignment/${assignment_id}/pairs/?page=${page}&per_page=${per_page}`
    axios
      .get(url)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  archivePair: function(pairingId, cb, errCb) {
    const data = { archived: true }
    axios
      .put(`/api/pairing/${pairingId}/`, data)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  scheduleAutomaticPairing: function(data, cb, errCb) {
    axios
      .post("/api/pairing/automatic/schedule/", data)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  scheduleCSVPairup: function(data, cb, errCb) {
    axios
      .post("/api/pairing/csv/schedule/", data)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  getAllGroups: function(data, cb, errCb) {
    let { course_id, assignment_id } = data
    let url = `/api/course/${course_id}/assignment/${assignment_id}/groups/`
    axios
      .get(url)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
}
