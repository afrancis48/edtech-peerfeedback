import assignmentAPI from "../../api/assignment"

export const state = {
  isLoading: false,
  all: [],
  current: {},
  settings: {},
  settingsLoading: false,
  settingsNotExist: false,
  tas: [],
  tasLoading: false,
  peers: [],
  peersLoading: false,
  metrics: null,
  metricsLoading: false
}

export const getters = {
  regular: function(state) {
    return state.all.filter(a => !a.intra_group_review)
  },
  igrs: function(state) {
    return state.all.filter(a => a.intra_group_review)
  }
}

export const mutations = {
  setLoading: function(state, payload) {
    if (typeof payload === "boolean") state.isLoading = payload
  },
  setAssignments: function(state, assignments) {
    if (Array.isArray(assignments)) state.all = assignments
  },
  setCurrentAssignment: function(state, assignment) {
    if (typeof assignment === "object") state.current = assignment
  },
  setSettings: function(state, settings) {
    if (typeof settings === "object") state.settings = settings
    if (state.settings.rubric_id === null) state.settings.rubric_id = 0
  },
  setSettingsLoading: function(state, payload) {
    if (typeof payload === "boolean") state.settingsLoading = payload
  },
  setTAs: function(state, payload) {
    if (Array.isArray(payload)) state.tas = payload
  },
  setTAsLoading: function(state, payload) {
    if (typeof payload === "boolean") state.tasLoading = payload
  },
  setPeers: function(state, payload) {
    if (Array.isArray(payload)) state.peers = payload
  },
  setPeersLoading: function(state, payload) {
    if (typeof payload === "boolean") state.peersLoading = payload
  },
  setSettingsNotExist: function(state, payload) {
    if (typeof payload === "boolean") state.settingsNotExist = payload
  },
  setMetrics: function(state, payload) {
    if (typeof payload === "object") state.metrics = payload
  },
  setMetricsLoading: function(state, payload) {
    if (typeof payload == "boolean") state.metricsLoading = payload
  }
}

export const actions = {
  getAssignmentsInCourse: function({ commit, dispatch }, course_id) {
    commit("setLoading", true)
    assignmentAPI.getCourseAssignments(
      course_id,
      assigns => {
        commit("setAssignments", assigns)
        commit("setLoading", false)
      },
      error => {
        let { status, statusText } = error.response
        const errMsg = {
          message: `Failed to get the assignments. ${status} ${statusText}`,
          level: "error"
        }
        dispatch("postMessage", errMsg, { root: true })
        commit("setLoading", false)
      }
    )
  },
  setCurrent: function({ commit, state }, ids) {
    let assignment = state.all.find(a => a.id === ids.assignment_id)
    if (typeof assignment !== "undefined") {
      commit("setCurrentAssignment", assignment)
      return
    }
    commit("setLoading", true)
    assignmentAPI.getAssignment(ids, assign => {
      commit("setCurrentAssignment", assign)
      commit("setLoading", false)
    })
  },
  loadSettings: function({ commit }, ids) {
    commit("setSettingsLoading", true)
    assignmentAPI.getSettings(
      ids,
      setting => {
        commit("setSettings", setting)
        commit("setSettingsNotExist", false)
        commit("setSettingsLoading", false)
      },
      () => {
        commit("setSettingsNotExist", true)
        commit("setSettingsLoading", false)
      }
    )
  },
  updateSettings: function({ state, commit }, action) {
    return new Promise((resolve, reject) => {
      assignmentAPI.updateSettings(
        { ...state.settings, on_rubric_change: action },
        settings => {
          commit("setSettings", settings)
          resolve(settings)
        },
        reject
      )
    })
  },
  getTAsAllotments: function({ commit }, ids) {
    commit("setTAsLoading", true)
    assignmentAPI.getTAsWithAllotments(
      ids,
      tas => {
        commit("setTAs", tas)
        commit("setTAsLoading", false)
      },
      () => {
        commit("setTAsLoading", false)
      }
    )
  },
  allotStudentsToTAs: function(context, payload) {
    return new Promise((resolve, reject) =>
      assignmentAPI.allotTAs(payload, resolve, reject)
    )
  },
  getPeers: function({ commit }, ids) {
    commit("setPeersLoading", true)
    assignmentAPI.getPeers(
      ids,
      peers => {
        commit("setPeers", peers)
        commit("setPeersLoading", false)
      },
      err => {
        console.log(err)
        commit("setPeersLoading", false)
      }
    )
  },
  getAffectedByRubricChange: function({ state }) {
    return new Promise((resolve, reject) => {
      assignmentAPI.getRubricChangeEffect(state.settings.id, resolve, reject)
    })
  },
  getTaskMetrics: function({ commit }, params) {
    commit("setMetricsLoading", true)
    assignmentAPI.fetchTaskMetrics(
      params,
      metrics => {
        commit("setMetrics", metrics)
        commit("setMetricsLoading", false)
      },
      err => {
        console.log(err)
        commit("setMetricsLoading", false)
      }
    )
  }
}

export default {
  namespaced: true,
  state,
  getters,
  mutations,
  actions
}
