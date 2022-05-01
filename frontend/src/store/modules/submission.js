import submissionAPI from "../../api/submission"

export const state = {
  current: null,
  isLoading: false
}

export const mutations = {
  setCurrent: function(state, payload) {
    if (typeof payload === "object") state.current = payload
  },
  setLoading: function(state, payload) {
    if (typeof payload === "boolean") state.isLoading = payload
  },
  clearCurrent: function(state) {
    state.current = null
  }
}

export const getters = {}

export const actions = {
  getSubmission: function({ commit }, ids) {
    commit("clearCurrent")
    commit("setLoading", true)
    submissionAPI.getSubmission(
      ids,
      sub => {
        commit("setCurrent", sub)
        commit("setLoading", false)
      },
      () => {
        commit("setLoading", false)
      }
    )
  },
  refetchSubmission: function({ commit, dispatch }, ids) {
    commit("setLoading", true)
    submissionAPI
      .retryGetSubmission(ids)
      .then(() => dispatch("getSubmission", ids))
      .catch(() => dispatch("getSubmission", ids))
  }
}

export default {
  namespaced: true,
  state,
  mutations,
  getters,
  actions
}
