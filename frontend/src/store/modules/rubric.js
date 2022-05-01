import rubricAPI from "../../api/rubric"

export const state = {
  all: [],
  isLoading: false,
  loadingList: [],
  current: {
    name: "",
    description: "",
    makePublic: false,
    criterions: []
  },
  currentLoading: false
}

export const mutations = {
  setLoading: function(state, payload) {
    if (typeof payload === "boolean") state.isLoading = payload
  },
  setAll: function(state, payload) {
    if (Array.isArray(payload)) state.all = payload
  },
  addRubric: function(state, payload) {
    let existing = state.all.find(r => r.id === payload.id)
    if (typeof existing === "undefined") {
      state.all.push(payload)
    } else {
      state.all.splice(state.all.indexOf(existing), 1, payload)
    }
  },
  setCurrentRubric: function(state, payload) {
    if (typeof payload === "object") state.current = payload
  },
  setAsCurrent: function(state, id) {
    if (typeof id !== "number") return
    let rubric = state.all.find(r => r.id === id)
    if (rubric) state.current = rubric
  },
  addToLoading: function(state, payload) {
    if (typeof payload !== "number") return
    if (!state.isLoading) state.isLoading = true
    state.loadingList.push(payload)
  },
  removeFromLoading: function(state, payload) {
    if (typeof payload !== "number") return
    let location = state.loadingList.indexOf(payload)
    if (location === -1) return
    state.loadingList.splice(location, 1)
    if (!state.loadingList.length) state.isLoading = false
  },
  updateRubric: function(state, payload) {
    if (typeof payload !== "object") return
    let existing = state.all.find(r => r.id === payload.id)
    let index = state.all.indexOf(existing)
    state.all[index] = payload
  }
}

export const getters = {
  rubricWithId: function(state) {
    return id => state.all.find(rubric => rubric.id === id)
  }
}

export const actions = {
  getAllRubrics: function({ commit }) {
    commit("setLoading", true)
    rubricAPI.getRubrics(rubrics => {
      commit("setAll", rubrics)
      commit("setLoading", false)
    })
  },
  createNewRubric: function({ commit }, payload) {
    return new Promise((resolve, reject) => {
      rubricAPI.createNewRubric(
        payload,
        rubric => {
          commit("addRubric", rubric)
          resolve(rubric)
        },
        reject
      )
    })
  },
  getRubricWithCriterions: function({ state, commit }, id) {
    // skip api call if already loading
    if (state.loadingList.indexOf(id) !== -1) return

    commit("addToLoading", id)
    return new Promise((resolve, reject) => {
      rubricAPI.getRubric(
        id,
        rubric => {
          commit("addRubric", rubric)
          commit("removeFromLoading", rubric.id)
          resolve(rubric)
        },
        err => {
          commit("setLoading", false)
          reject(err)
        }
      )
    })
  },
  setCurrent: function({ commit, state }, id) {
    let rubric = state.all.find(r => r.id === id)
    if (typeof rubric !== "undefined" && rubric.hasOwnProperty("criterions")) {
      commit("setCurrentRubric", rubric)
      return
    }
    commit("setLoading", true)
    rubricAPI.getRubric(
      id,
      rubric => {
        commit("addRubric", rubric)
        commit("setCurrentRubric", rubric)
        commit("setLoading", false)
      },
      () => {
        commit("setLoading", false)
      }
    )
  },
  loadMyRubrics: function({ commit }) {
    commit("setLoading", true)
    rubricAPI.getMyRubrics(
      rubrics => {
        commit("setAll", rubrics)
        commit("setLoading", false)
      },
      err => {
        console.log("Failed to fetch user's rubrics", err)
      }
    )
  },
  togglePublic: function({ commit }, rubric) {
    rubricAPI.updateRubric(
      rubric.id,
      { public: !rubric.public },
      r => commit("updateRubric", r),
      err => console.log("Failed to update rubric", err)
    )
  },
  toggleActive: function({ commit }, rubric) {
    rubricAPI.updateRubric(
      rubric.id,
      { active: !rubric.active },
      r => commit("updateRubric", r),
      err => console.log("Failed to update rubric", err)
    )
  }
}

export default {
  namespaced: true,
  state,
  mutations,
  getters,
  actions
}
