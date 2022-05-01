const state = {
  all: [],
  counter: 0
}

export const mutations = {
  addMessage(state, payload) {
    state.all.push(payload)
    state.counter++
  }
}

export const actions = {
  postMessage: {
    root: true,
    handler({ commit, state }, payload) {
      let msgItem = {
        id: state.counter,
        message: "",
        level: "info",
        action: "ignore"
      }
      if (typeof payload === "string") msgItem.message = payload
      else if (typeof payload === "object") {
        if (!payload.hasOwnProperty("message")) return
        msgItem.message = payload.message
        msgItem.level = payload.level || "info"
        msgItem.action = payload.action || "ignore"
      }
      commit("addMessage", msgItem)
    }
  }
}

export const getters = {}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations
}
