import axios from "axios"

export default {
  getCommentsForSubmission: function(
    { course_id, assignment_id, user_id },
    cb,
    errCb
  ) {
    axios
      .get(
        `/api/comment/?course_id=${course_id}&assignment_id=${assignment_id}&recipient_id=${user_id}`
      )
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  createNewComment: function(data, cb, errCb) {
    axios
      .post("/api/comment/", data)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  createLike: function(data, cb, errCb) {
    axios
      .post("/api/comment/like/", data)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  deleteLike: function(like_id, cb, errCb) {
    axios
      .delete(`/api/comment/like/${like_id}/`)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  }
}
