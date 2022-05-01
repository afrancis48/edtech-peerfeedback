import commentAPI from "../../api/comment"

export const state = {
  all: [],
  isLoading: false,
  addingComment: false
}

export const getters = {}

export const mutations = {
  setComments: function(state, payload) {
    if (!Array.isArray(payload)) return
    state.all = payload.sort((a, b) => {
      if (a.id < b.id) return -1
      if (a.id > b.id) return 1
      return 0
    })
  },
  setLoading: function(state, payload) {
    if (typeof payload === "boolean") state.isLoading = payload
  },
  addNewComment: function(state, payload) {
    if (typeof payload === "object") state.all.push(payload)
  },
  addLike: function(state, payload) {
    if (
      !payload.hasOwnProperty("comment_id") ||
      !payload.hasOwnProperty("likeObj")
    )
      return
    let comment = state.all.find(c => c.id === payload.comment_id)
    if (!comment.hasOwnProperty("likes")) return
    comment.likes.push(payload.likeObj)
  },
  removeLike(state, payload) {
    if (
      !payload.hasOwnProperty("comment_id") ||
      !payload.hasOwnProperty("like_id")
    )
      return
    let comment = state.all.find(c => c.id === payload.comment_id)
    if (!comment.hasOwnProperty("likes")) return
    comment.likes = comment.likes.filter(like => like.id !== payload.like_id)
  },
  setAddingComment: function(state, payload) {
    if (typeof payload === "boolean") state.addingComment = payload
  }
}

export const actions = {
  getComments: function({ commit }, ids) {
    commit("setComments", [])
    commit("setLoading", true)
    commentAPI.getCommentsForSubmission(
      ids,
      comments => {
        commit("setComments", comments)
        commit("setLoading", false)
      },
      err => {
        console.log(err)
        commit("setLoading", false)
      }
    )
  },
  addComment: function({ commit }, comment) {
    commit("setAddingComment", true)
    commentAPI.createNewComment(
      comment,
      c => {
        commit("addNewComment", c)
        commit("setAddingComment", false)
      },
      e => {
        commit("setAddingComment", false)
        // FIXME this is a quick fix solution
        throw e
      }
    )
  },
  likeComment: function({ commit }, comment_id) {
    commentAPI.createLike(
      { comment_id },
      likeObj => commit("addLike", { comment_id, likeObj }),
      err => console.log(err)
    )
  },
  unlikeComment: function({ commit }, ids) {
    commentAPI.deleteLike(
      ids.like_id,
      () => commit("removeLike", ids),
      err => console.log(err)
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
