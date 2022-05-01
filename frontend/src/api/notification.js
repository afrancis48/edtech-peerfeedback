import axios from "axios"

export default {
  getAll(cb, errCb) {
    axios
      .get("/api/notifications/")
      .then(response => cb(response.data))
      .catch(error => errCb(error))
  },

  markAsRead(notification, cb, errCb) {
    axios
      .put(`/api/notification/${notification.id}/`, { read: true })
      .then(res => cb(res.data))
      .catch(err => errCb(err))
  },

  clearAll(cb, errCb) {
    axios
      .post("/api/notifications/clear/")
      .then(res => cb(res.data))
      .catch(err => errCb(err))
  },

  sendPendingReminder(course, assignment, user) {
    if (!user) {
      return axios.post(
        `/api/course/${course}/assignment/${assignment}/notify/all/`
      )
    }
    return axios.post(
      `/api/course/${course}/assignment/${assignment}/user/${user}/notify/`
    )
  }
}
