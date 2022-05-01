import feedbackAPI from "../../api/feedback"

export const state = {
  all: [],
  isLoading: false,
  extra: {},
  extraLoading: false,
  current: null,
  currentLoading: false,
  currentUpdating: false,
  extrasGiven: 0,
  previousReadTime: 0,
  previousWriteTime: 0,
  hasMore: false,
  currentPage: 1,
  totalFeedback: 0,
  deletingExtra: false,
  aiScore: -1,
  aiConfidence: -1,
  aiScoreLoading: false
}

export const getters = {}

export const mutations = {
  setFeedbacks: function(state, payload) {
    if (!Array.isArray(payload)) return
    state.all = payload
  },
  addFeedback: function(state, payload) {
    if (Array.isArray(payload)) state.all.push(...payload)
    else if (typeof payload === "object") state.all.push(payload)
  },
  setLoading: function(state, payload) {
    if (typeof payload === "boolean") state.isLoading = payload
  },
  setExtra: function(state, payload) {
    if (typeof payload === "object") state.extra = payload
  },
  setExtraLoading: function(state, payload) {
    if (typeof payload === "boolean") state.extraLoading = payload
  },
  setCurrent: function(state, payload) {
    if (typeof payload === "object") state.current = payload
  },
  setCurrentLoading: function(state, payload) {
    if (typeof payload === "boolean") state.currentLoading = payload
  },
  addRatingToFeedback: function(state, payload) {
    if (typeof payload !== "object") return
    let feedback = state.all.find(fb => fb.id === payload.feedback_id)
    feedback.rating = payload
  },
  setExtrasGiven: function(state, payload) {
    if (Number.isNaN(parseInt(payload))) return
    state.extrasGiven = parseInt(payload)
  },
  setCurrentUpdating: function(state, payload) {
    if (typeof payload === "boolean") state.currentUpdating = payload
  },
  updateCurrentFeedbackComment: function(state, payload) {
    if (typeof payload === "string") state.current.value = payload
  },
  setPreviousTimes: function(state, payload) {
    if (payload.hasOwnProperty("read_time"))
      state.previousReadTime = payload.read_time
    if (payload.hasOwnProperty("write_time"))
      state.previousWriteTime = payload.write_time
  },
  updateReadingTime: function(state, payload) {
    if (Number.isFinite(payload))
      state.readTime = state.previousReadTime + payload
  },
  setCurrentPage: function(state, payload) {
    if (payload.hasOwnProperty("has_next")) state.hasMore = payload.has_next
    if (payload.hasOwnProperty("page")) state.currentPage = payload.page
    if (payload.hasOwnProperty("total")) state.totalFeedback = payload.total
  },
  clearAll: function(state) {
    state.all.length = 0
  },
  setDeletingExtra: function(state, payload) {
    if (typeof payload === "boolean") state.deletingExtra = payload
  },
  clearExtra: function(state) {
    state.extra = {}
  },
  setAIValues: function(state, ai) {
    if (ai.hasOwnProperty("class")) state.aiScore = ai.class
    if (ai.hasOwnProperty("confidence")) state.aiConfidence = ai.confidence
  },
  resetAIValues: function(state) {
    state.aiScore = -1
    state.aiConfidence = -1
  },
  setAIScoreLoading: function(state, payload) {
    state.aiScoreLoading = payload
  }
}

export const actions = {
  getExtraFeedbackRequest: function({ commit }, ids) {
    commit("setExtraLoading", true)
    feedbackAPI.getExtraFeedback(ids.course_id, ids.assignment_id, extra => {
      commit("setExtra", extra)
      commit("setExtraLoading", false)
    })
  },
  requestExtraFeedback: function({ commit, dispatch }, ids) {
    let msg = {
      message: "Your request for extra feedback has been registered.",
      level: "success"
    }
    feedbackAPI.requestExtraFeedback(
      ids,
      extra => {
        commit("setExtra", extra)
        dispatch("postMessage", msg, { root: true })
      },
      error => {
        msg.message =
          "Failed to raise a request for extra feedback. " + error.statusText
        msg.level = "error"
        dispatch("postMessage", msg, { root: true })
      }
    )
  },
  rateFeedback: function({ commit }, payload) {
    return new Promise((resolve, reject) => {
      feedbackAPI.postMetaFeedback(
        payload,
        rate => {
          commit("addRatingToFeedback", rate)
          resolve(rate)
        },
        reject
      )
    })
  },
  getSubmissionFeedbacks: function({ commit }, ids) {
    commit("setLoading", true)
    feedbackAPI.getFeedbacksForSubmission(
      ids,
      feeds => {
        commit("setFeedbacks", feeds)
        commit("setLoading", false)
      },
      err => {
        console.log(err)
        commit("setLoading", false)
      }
    )
  },
  getExtraFeedbackGiven: function({ commit }, ids) {
    feedbackAPI.getExtrasGivenCount(ids, count =>
      commit("setExtrasGiven", count)
    )
  },
  getMyFeedbackForSubmission: function({ commit }, ids) {
    commit("setCurrentLoading", true)
    feedbackAPI.getMyFeedback(
      ids,
      fb => {
        commit("setCurrent", fb)
        commit("setPreviousTimes", fb)
        commit("setCurrentLoading", false)
      },
      err => {
        console.log(err)
        commit("setCurrentLoading", false)
      }
    )
  },
  updateCurrentFeedback: function({ commit, state }, data) {
    commit("setCurrentUpdating", true)
    if (!(state.current.hasOwnProperty("id") && state.current.draft)) {
      console.error("Cannot update current feedback. ", state.current)
      return
    }
    // update the comment in local store before the server updates
    let old_value = state.current.value
    commit("updateCurrentFeedbackComment", data.value)
    if (state.readTime) data.read_time = state.readTime

    return new Promise((resolve, reject) => {
      feedbackAPI.updateFeedback(
        state.current.id,
        data,
        fb => {
          commit("setCurrent", fb)
          commit("setCurrentUpdating", false)
          if (!fb.draft) commit("addFeedback", fb)
          resolve(fb)
        },
        err => {
          commit("updateCurrentFeedbackComment", old_value)
          commit("setCurrentUpdating", false)
          reject(err)
        }
      )
    })
  },
  getAllFeedback: function({ commit }, params) {
    commit("setLoading", true)
    if (params.page === 1) commit("clearAll")
    feedbackAPI.getAllUserFeedback(
      params,
      resp => {
        if (resp.page === 1) {
          commit("setFeedbacks", resp.feedback)
        } else {
          commit("addFeedback", resp.feedback)
        }
        commit("setCurrentPage", resp)
        commit("setLoading", false)
      },
      err => {
        console.log(err)
        commit("setLoading", false)
      }
    )
  },
  deleteExtraRequest: function({ state, commit }) {
    if (!state.extra.hasOwnProperty("id")) return
    commit("setDeletingExtra", true)
    feedbackAPI.deleteExtraFeedbackRequest(
      state.extra.id,
      () => {
        commit("setDeletingExtra", false)
        commit("clearExtra")
      },
      err => {
        commit("setDeletingExtra", false)
        console.log(err)
      }
    )
  },
  getAIQualityScore: function({ state, commit }, value) {
    if (state.aiScoreLoading) return
    commit("setAIScoreLoading", true)
    feedbackAPI.getAIScore(
      value,
      data => {
        commit("setAIScoreLoading", false)
        commit("setAIValues", data)
      },
      err => {
        commit("setAIScoreLoading", false)
        console.log(err)
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
