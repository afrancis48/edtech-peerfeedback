import axios from "axios"
import { authHead } from "./common"

export default {
  refreshLogin(token, cb, errCb) {
    axios
      .post("/users/login/refresh/", {}, authHead(token))
      .then(response => {
        let tokens = response.data
        if (tokens.hasOwnProperty("access_token")) {
          axios.defaults.headers.common["Authorization"] =
            "Bearer " + tokens["access_token"]
        }
        cb(tokens)
      })
      .catch(error => errCb(error))
  },
  logout(cb, errCb) {
    axios
      .post("/users/logout/")
      .then(() => cb())
      .catch(err => errCb(err))
  },
  getProfile(cb, errCb) {
    axios
      .get("/users/profile/")
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  updateProfile(data, cb, errCb) {
    axios
      .put("/users/profile/", data)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  getUserSettings(cb, errCb) {
    axios
      .get("/users/settings/")
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  updateUserSettings(data, cb, errCb) {
    axios
      .put("/users/settings/", data)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  getProfileOfUser(id, cb, errCb) {
    axios
      .get(`/users/${id}/profile/`)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  getMedalsOfUser(id, cb, errCb) {
    axios
      .get(`/api/medals/?user=${id}`)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  sendHelpEmail(email, cb, errCb) {
    axios
      .post(`/api/support/email/`, email)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  }
}
