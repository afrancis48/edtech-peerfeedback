import taskAPI from "../../api/task"

export const state = {
  tasks: [],
  isLoading: false,
  current: null,
  currentLoading: false,
  noSubmissionTask: true
}

export const getters = {
  incompleteTasks: function(state) {
    return state.tasks.filter(task => task.status !== "COMPLETE")
  }
}

export const actions = {
  getCourseTasks: function({ commit }, course_id) {
    commit("setLoading", true)
    taskAPI.getCourseTasks(course_id, tasks => {
      commit("setTasks", tasks)
      commit("setLoading", false)
    })
  },
  getTaskForSubmission: function({ commit, state }, payload) {
    commit("clearCurrent")
    commit("setCurrentLoading", true)
    if (!payload.hasOwnProperty("force") || !payload.force) {
      let task = state.tasks.find(
        t =>
          t.course_id === payload.course_id &&
          t.assignment_id === payload.assignment_id &&
          t.pairing.recipient.id === payload.user_id
      )
      if (typeof task !== "undefined") {
        commit("setCurrent", task)
        commit("setCurrentLoading", false)
        return
      }
    }
    taskAPI.getSubmissionTask(
      payload,
      task => {
        commit("setCurrent", task)
        commit("setCurrentLoading", false)
      },
      () => {
        commit("setCurrentLoading", false)
      }
    )
  },
  getIncompleteTasks: function({ commit }) {
    commit("setLoading", true)
    taskAPI.getAllIncompleteTasks(
      tasks => {
        commit("setTasks", tasks)
        commit("setLoading", false)
      },
      err => {
        console.error(err)
        commit("setLoading", false)
      }
    )
  },
  archiveTask: function({ commit }, task_id) {
    commit("setArchiving", task_id)
    taskAPI.archiveTask(
      task_id,
      task => commit("removeTask", task),
      err => {
        console.error(err)
        commit("unsetArchiving", task_id)
      }
    )
  },
  replaceAndGetNewTask: function({ state }) {
    if (!state.current.hasOwnProperty("id")) {
      console.error("No current task set to replace.")
      return
    }

    return new Promise((resolve, reject) =>
      taskAPI.replaceTask(state.current.id, resolve, reject)
    )
  }
}

export const mutations = {
  setTasks: function(state, payload) {
    if (Array.isArray(payload)) state.tasks = payload
  },
  setLoading: function(state, payload) {
    if (typeof payload === "boolean") state.isLoading = payload
  },
  setCurrent: function(state, payload) {
    if (typeof payload === "object") {
      state.current = payload
      state.noSubmissionTask = false
    }
  },
  clearCurrent: function(state) {
    state.current = null
    state.noSubmissionTask = true
  },
  setCurrentLoading: function(state, payload) {
    if (typeof payload === "boolean") state.currentLoading = payload
  },
  setArchiving: function(state, payload) {
    if (!Number.isInteger(payload)) return
    let task = state.tasks.find(item => item.id === payload)
    if (typeof task === "undefined") return
    task.archiving = true
  },
  unsetArchiving: function(state, payload) {
    if (!Number.isInteger(payload)) return
    let task = state.tasks.find(item => item.id === payload)
    if (typeof task === "undefined") return
    task.archiving = false
  },
  removeTask: function(state, payload) {
    if (payload.hasOwnProperty("id"))
      state.tasks = state.tasks.filter(task => task.id !== payload.id)
  }
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations
}
