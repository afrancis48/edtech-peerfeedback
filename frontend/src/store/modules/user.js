import axios from "axios"
import userAPI from "../../api/user"
import { getIdentity, getCookie, getExpiry } from "../../utils"

const state = {
  accessToken: "",
  avatar_url: "https://api.adorable.io/avatars/50/guest@peerfeedback.io.png",
  refreshToken: "",
  roles: [],
  profile: {},
  profileLoading: false,
  updating: false,
  settings: null,
  settingsLoading: false,
  medals: [],
  medalsLoading: false,
  sendingSupportMail: false
}

export const getters = {
  isLoggedIn: state => {
    return state.accessToken !== "" && state.accessToken !== null
  },
  hasRefreshToken: state => {
    return state.refreshToken !== "" && state.refreshToken !== null
  },
  currentUser: state => {
    return getIdentity(state.accessToken)
  },
  showSubmissionWarning: state => {
    return state.settings.submission_warning
  }
}

export const actions = {
  async loadTokens({ commit, dispatch }) {
    let tokens = {}
    tokens.access_token = getCookie("access_token")
    tokens.refresh_token =
      getCookie("refresh_token") || localStorage.getItem("refreshToken")
    if (tokens.refresh_token === "null" || tokens.refresh_token === null) {
      tokens.refresh_token = ""
    }
    commit("setTokens", tokens)

    if (tokens.access_token.length) {
      axios.defaults.headers.common["Authorization"] =
        "Bearer " + tokens.access_token
      let expiry = getExpiry(tokens.access_token) - new Date() - 5000
      setTimeout(() => dispatch("refreshAccessToken"), expiry)
    } else if (tokens.refresh_token.length) {
      await dispatch("refreshAccessToken")
    }
  },
  refreshAccessToken({ commit, dispatch, state }) {
    return new Promise((resolve, reject) => {
      userAPI.refreshLogin(
        state.refreshToken,
        tokens => {
          commit("setTokens", tokens)
          let expiry = getExpiry(tokens.access_token) - new Date() - 5000
          setTimeout(() => dispatch("refreshAccessToken"), expiry)
          resolve()
        },
        () => {
          commit("clearTokens")
          reject()
        }
      )
    })
  },
  logout({ commit }) {
    userAPI.logout(() => commit("clearTokens"), () => commit("clearTokens"))
  },
  getProfile({ commit }) {
    commit("setProfileLoading", true)
    userAPI.getProfile(
      profile => {
        commit("setProfile", profile)
        commit("setProfileLoading", false)
      },
      err => {
        console.log(err)
        commit("setProfileLoading", false)
      }
    )
  },
  updateProfile({ commit, state }) {
    commit("setUpdating", true)
    userAPI.updateProfile(
      state.profile,
      () => {
        commit("setUpdating", false)
      },
      err => {
        console.log(err)
        commit("setUpdating", false)
      }
    )
  },
  getSettings({ commit }) {
    commit("setSettingsLoading", true)
    userAPI.getUserSettings(
      set => {
        commit("setSettings", set)
        commit("setSettingsLoading", false)
      },
      err => {
        console.log(err)
        commit("setSettingsLoading", false)
      }
    )
  },
  updateSettings({ commit, state }) {
    commit("setUpdating", true)
    userAPI.updateUserSettings(
      state.settings,
      set => {
        commit("setSettings", set)
        commit("setUpdating", false)
      },
      err => {
        console.log(err)
        commit("setUpdating", false)
      }
    )
  },
  getProfileOfUser({ commit }, id) {
    commit("setProfileLoading", true)
    userAPI.getProfileOfUser(
      id,
      profile => {
        commit("setProfile", profile)
        commit("setProfileLoading", false)
      },
      err => {
        console.log(err)
        commit("setProfileLoading", false)
      }
    )
  },
  getMedalsOfUser({ commit }, id) {
    commit("setMedalsLoading", true)
    userAPI.getMedalsOfUser(
      id,
      medals => {
        commit("setMedals", medals)
        commit("setMedalsLoading", false)
      },
      err => {
        console.log(err)
        commit("setMedalsLoading", false)
      }
    )
  },
  sendSupportEmail({ commit }, email) {
    commit("setSendingSupportMail", true)
    userAPI.sendHelpEmail(
      email,
      () => {
        commit("setSendingSupportMail", false)
      },
      err => {
        console.log(err)
        commit("setSendingSupportMail", false)
      }
    )
  },
  disableSubmissionWarning({ commit }) {
    userAPI.updateUserSettings(
      { submission_warning: false },
      data => commit("setSettings", data),
      err => console.log(err)
    )
  }
}

export const mutations = {
  setTokens(state, payload) {
    if (typeof payload === "undefined") {
      state.refreshToken = state.accessToken = ""
      return
    }

    if (payload.hasOwnProperty("refresh_token")) {
      state.refreshToken = payload["refresh_token"]
      localStorage.setItem("refreshToken", payload["refresh_token"])
    }
    if (payload.hasOwnProperty("access_token")) {
      state.accessToken = payload["access_token"]
    }
  },
  clearTokens(state) {
    state.refreshToken = ""
    state.accessToken = ""
    localStorage.removeItem("refreshToken")
  },
  setProfile(state, payload) {
    if (typeof payload === "object") state.profile = payload
  },
  setProfileLoading(state, payload) {
    if (typeof payload === "boolean") state.profileLoading = payload
  },
  setUpdating(state, payload) {
    if (typeof payload === "boolean") state.updating = payload
  },
  setSettings(state, payload) {
    if (typeof payload === "object") state.settings = payload
  },
  setSettingsLoading(state, payload) {
    if (typeof payload === "boolean") state.settingsLoading = payload
  },
  setMedals(state, payload) {
    if (Array.isArray(payload)) state.medals = payload
  },
  setMedalsLoading(state, payload) {
    if (typeof payload === "boolean") state.medalsLoading = payload
  },
  setSendingSupportMail(state, payload) {
    if (typeof payload === "boolean") state.sendingSupportMail = payload
  }
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations
}
