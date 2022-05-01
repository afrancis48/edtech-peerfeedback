import courseAPI from "../../api/course"

export const state = {
  courses: [],
  current: null,
  isLoading: true,
  students: [],
  tas: []
}

export const getters = {
  role: function(state) {
    if (state.current === null) return false
    if (!state.current.hasOwnProperty("enrollments")) return false
    if (!state.current.enrollments.length) return "not_enrolled"
    return state.current.enrollments[0].type
  },
  activeCourses: function(state) {
    const now = new Date()
    return state.courses.filter(course => {
      if (course.end_at) {
        return new Date(course.end_at) > now
      } else if (course.term && course.term.end_at) {
        return new Date(course.term.end_at) > now
      }
      // if there are no dates, make sure it is at least marked as available
      return course.workflow_state === "available"
    })
  },
  inactiveCourses: function(state) {
    const now = new Date()
    return state.courses.filter(course => {
      if (course.end_at) {
        return new Date(course.end_at) < now
      } else if (course.term && course.term.end_at) {
        return new Date(course.term.end_at) < now
      }
      return course.workflow_state !== "available"
    })
  }
}

export const mutations = {
  setCourses: function(state, payload) {
    if (Array.isArray(payload)) state.courses = payload
  },
  setLoading: function(state, payload) {
    if (typeof payload !== "boolean") return
    state.isLoading = payload
  },
  setCurrentCourse: function(state, course) {
    if (typeof course === "object" && course.hasOwnProperty("name"))
      state.current = course
  },
  clearCurrentCourse: function(state) {
    state.current = null
  },
  clearStudents: function(state) {
    state.students = []
  },
  setStudents: function(state, payload) {
    if (Array.isArray(payload)) state.students = payload
  },
  setTAs: function(state, payload) {
    if (Array.isArray(payload)) state.tas = payload
  }
}

export const actions = {
  getCourses: function({ dispatch, commit }) {
    commit("setLoading", true)
    courseAPI.getAllCourses(
      courses => {
        commit("setCourses", courses)
        commit("setLoading", false)
      },
      error => {
        let { status, statusText } = error.response
        let errorMsg = {
          message: `Failed to fetch courses. ${status} ${statusText}`,
          level: "error"
        }
        dispatch("postMessage", errorMsg, { root: true })
        commit("setLoading", false)
      }
    )
  },
  setCurrent: function({ commit, state }, course_id) {
    commit("clearCurrentCourse")
    commit("clearStudents")
    let course = state.courses.find(c => c.id === course_id)
    if (typeof course !== "undefined") {
      commit("setCurrentCourse", course)
      return
    }
    commit("setLoading", true)
    courseAPI.getCourse(course_id, course => {
      commit("setCurrentCourse", course)
      commit("setLoading", false)
    })
  },
  getStudents: function({ commit }, course_id) {
    courseAPI.getStudents(course_id, students =>
      commit("setStudents", students)
    )
  },
  getTAs: function({ commit }, course_id) {
    courseAPI.getTAs(course_id, tas => commit("setTAs", tas))
  },
  setupCourse: function(context, course_id) {
    return new Promise((resolve, reject) => {
      courseAPI.initializeCourse(course_id, resolve, reject)
    })
  }
}

export default {
  namespaced: true,
  state,
  getters,
  mutations,
  actions
}
