import axios from "axios"

export default function createActionQueueModerator() {
  return store => {
    const queue = []
    let shouldQueue = true

    axios.interceptors.response.use(
      function(response) {
        return response
      },
      function(error) {
        // If the network error is a 401 for getting a new access token, then logout
        if (
          typeof error.response !== "undefined" &&
          error.response.status === 401 &&
          error.response.config.url.includes("/login/refresh/")
        ) {
          store.dispatch("user/logout")
        }
        return Promise.reject(error)
      }
    )

    store.subscribe((mutation, state) => {
      if (mutation.type === "user/setTokens" && state.user.accessToken !== "") {
        shouldQueue = false
        queue.forEach(action => {
          store.dispatch(action)
        })
        queue.length = 0
      }
    })
    store.subscribeAction(action => {
      switch (action.type) {
        case "user/refreshAccessToken":
          shouldQueue = true
          break
        case "user/loadTokens":
        case "postMessage":
          break
        default:
          if (shouldQueue) queue.push(action)
      }
    })
  }
}
