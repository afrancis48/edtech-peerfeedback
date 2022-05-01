import pairingAPI from "../../api/pairing"
import jobsAPI from "../../api/job"

export const state = {
  all: [],
  isLoading: false,
  searching: false,
  searchResults: [],
  jobs: [],
  jobsLoading: false,
  pageCount: 0,
  autoScheduledJob: null,
  csvScheduledJob: null
}

export const getters = {
  autoJob: function(state) {
    return (course, assignment) => {
      let job = state.jobs.find(
        j =>
          j.pairing === "automatic" &&
          j.course_id === course &&
          j.assignment_id === assignment
      )
      return typeof job === "undefined" ? false : job
    }
  },
  csvJob: function(state) {
    let job = state.jobs.find(j => j.pairing === "csv")
    return typeof job === "undefined" ? false : job
  }
}

export const mutations = {
  setLoading: function(state, payload) {
    if (typeof payload === "boolean") state.isLoading = payload
  },
  setAll: function(state, payload) {
    if (Array.isArray(payload)) state.all = payload
  },
  clearAll: function(state) {
    state.all.length = 0
  },
  setJobs: function(state, payload) {
    if (Array.isArray(payload)) state.jobs = payload
  },
  setJobsLoading: function(state, payload) {
    if (typeof payload === "boolean") state.jobsLoading = payload
  },
  clearJobs: function(state) {
    state.jobs.length = 0
  },
  setSearching: function(state, payload) {
    if (typeof payload === "boolean") state.searching = payload
  },
  setResults: function(state, payload) {
    if (Array.isArray(payload)) state.searchResults = payload
  },
  setPageCount: function(state, payload) {
    if (Number.isInteger(payload)) state.pageCount = payload
  },
  removePair: function(state, pair) {
    if (!pair.hasOwnProperty("grader")) return
    let graderIdx = state.all.findIndex(row => row.grader.id === pair.grader.id)
    state.all[graderIdx].pairing = state.all[graderIdx].pairing.filter(
      p => p.id !== pair.id
    )
  },
  setAutoScheduledJob: function(state, job) {
    if (typeof job === "object" && job.hasOwnProperty("id")) {
      state.autoScheduledJob = job
    } else {
      state.autoScheduledJob = null
    }
  },
  setCSVScheduledJob: function(state, job) {
    if (typeof job === "object" && job.hasOwnProperty("id")) {
      state.csvScheduledJob = job
    } else {
      state.csvScheduledJob = null
    }
  }
}

export const actions = {
  getAssignmentPairs: function({ commit }, ids) {
    commit("clearAll")
    commit("setLoading", true)
    pairingAPI.getPairings(
      ids,
      data => {
        commit("setAll", data.pairs)
        commit("setLoading", false)
      },
      err => {
        console.log(err)
      }
    )
  },
  createAutomaticPairing: function(context, data) {
    return new Promise((resolve, reject) => {
      pairingAPI.createAutoPairs(data, resolve, reject)
    })
  },
  scheduleAutoPairing: function(context, data) {
    return new Promise((resolve, reject) => {
      pairingAPI.scheduleAutomaticPairing(data, resolve, reject)
    })
  },
  createManualPairing: function(context, data) {
    return new Promise((resolve, reject) => {
      pairingAPI.createManualPairs(data, resolve, reject)
    })
  },
  createCSVPairing: function(context, data) {
    return new Promise((resolve, reject) => {
      pairingAPI.createCSVPairs(data, resolve, reject)
    })
  },
  scheduleCSVPairing: function(context, data) {
    return new Promise((resolve, reject) => {
      pairingAPI.scheduleCSVPairup(data, resolve, reject)
    })
  },
  pairUser: function(context, data) {
    return new Promise((resolve, reject) => {
      pairingAPI.createPairing(data, resolve, reject)
    })
  },
  fetchActiveJobs: function({ commit }) {
    commit("clearJobs")
    commit("setJobsLoading", true)
    pairingAPI.getActiveJobs(
      jobs => {
        commit("setJobsLoading", false)
        commit("setJobs", jobs)
      },
      () => {
        commit("setJobsLoading", false)
      }
    )
  },
  searchPairings: function({ commit }, data) {
    commit("setSearching", true)
    pairingAPI.searchPairings(
      data,
      pairs => {
        commit("setResults", pairs)
        commit("setSearching", false)
      },
      err => {
        console.log(err)
        commit("setSearching", false)
      }
    )
  },
  getMyAssignmentPairs: function({ commit }, data) {
    commit("clearAll")
    commit("setLoading", true)
    data["mine"] = true
    pairingAPI.getPairings(
      data,
      pairs => {
        commit("setAll", pairs)
        commit("setLoading", false)
      },
      error => {
        console.log(error)
        commit("setLoading", false)
      }
    )
  },
  getPairingPage: function({ commit }, data) {
    commit("setLoading", true)
    pairingAPI.getPairingPage(
      data,
      data => {
        commit("setAll", data.pairs)
        if (data.hasOwnProperty("page_count"))
          commit("setPageCount", data.page_count)
        commit("setLoading", false)
      },
      err => {
        console.log("Failed to get pairing page", data, err)
        commit("setLoading", false)
      }
    )
  },
  archive: function({ commit }, pairingId) {
    pairingAPI.archivePair(
      pairingId,
      pair => commit("removePair", pair),
      err => {
        console.log(err.response)
      }
    )
  },
  getAutoSchedule: function({ commit }, assignmentId) {
    commit("setAutoScheduledJob", {})
    jobsAPI.getScheduledJob(
      assignmentId,
      "auto",
      job => {
        commit("setAutoScheduledJob", job)
      },
      err => {
        console.log(err.response)
      }
    )
  },
  getCSVSchedule: function({ commit }, assignmentId) {
    commit("setCSVScheduledJob", {})
    jobsAPI.getScheduledJob(
      assignmentId,
      "csv",
      job => commit("setCSVScheduledJob", job),
      err => console.log(err.response)
    )
  },
  cancelScheduled: function({ commit, state }, type) {
    if (
      (type === "auto" && !state.autoScheduledJob.hasOwnProperty("id")) ||
      (type === "csv" && !state.csvScheduledJob.hasOwnProperty("id"))
    )
      return
    let jobId =
      type === "auto" ? state.autoScheduledJob.id : state.csvScheduledJob.id

    jobsAPI
      .cancelScheduledJob(jobId)
      .then(() => {
        if (type === "auto") {
          commit("setAutoScheduledJob", {})
        } else {
          commit("setCSVScheduledJob", {})
        }
      })
      .catch(err => console.log(err))
  }
}

export default {
  namespaced: true,
  state,
  getters,
  mutations,
  actions
}
