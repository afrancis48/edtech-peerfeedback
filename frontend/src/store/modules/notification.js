import notificationAPI from "../../api/notification"

export const state = {
  notifications: []
}

function groupNotifications(notes) {
  // groups based on submissions
  let mappedNotes = notes.reduce((map, note) => {
    let key = note.assignment_id + "_" + note.user_id
    map[key] = map[key] || []
    map[key].push(note)
    return map
  }, {})

  return Object.keys(mappedNotes).map(key => {
    // sub-group by notifiers
    let notifierMap = mappedNotes[key]
      .sort((a, b) => b.id - a.id)
      .reduce((map, note) => {
        map[note.notifier.id] = map[note.notifier.id] || []
        map[note.notifier.id].push(note)
        return map
      }, {})
    let uniques = Object.keys(notifierMap).map(k => notifierMap[k][0])
    let firstNote = uniques[0]

    if (uniques.length > 2) {
      firstNote.notifier.name += ` and ${uniques.length - 1} others`
    } else if (uniques.length === 2) {
      firstNote.notifier.name += ` and ${uniques[1].notifier.name}`
    }
    return firstNote
  })
}

export const getters = {
  allNotifications: function(state) {
    return state.notifications
  },
  readNotifications: function(state) {
    return state.notifications.filter(note => note.read)
  },
  unreadNotifications: function(state) {
    return state.notifications.filter(note => !note.read)
  },
  groupedNotifications: function(state) {
    let commentNotes = state.notifications.filter(
      n => !n.read && n.item === "comment"
    )
    let likeNotes = state.notifications.filter(
      n => !n.read && n.item === "like"
    )
    let otherNotes = state.notifications.filter(
      n => n.item !== "comment" && n.item !== "like" && !n.read
    )
    commentNotes = groupNotifications(commentNotes)
    likeNotes = groupNotifications(likeNotes)
    otherNotes = [...otherNotes, ...commentNotes, ...likeNotes]
    otherNotes.sort((a, b) => b.id - a.id)
    return otherNotes
  }
}

export const mutations = {
  setAll: function(state, payload) {
    if (Array.isArray(payload)) {
      state.notifications = payload
    }
  },
  updateNotification: function(state, notification) {
    let index = state.notifications.findIndex(
      note => note.id === notification.id
    )
    state.notifications.splice(index, 1, notification)
  },
  markAllRead: function(state) {
    state.notifications.forEach(n => (n.read = true))
  }
}

export const actions = {
  getNotifications: function({ commit }) {
    notificationAPI.getAll(
      notes => commit("setAll", notes),
      err => {
        console.log(err)
      }
    )
  },
  markNotificationRead: function({ commit, state }, id) {
    let notification = state.notifications.find(note => note.id === id)
    if (typeof notification === "undefined") return
    notificationAPI.markAsRead(
      notification,
      note => commit("updateNotification", note),
      err => console.log(err)
    )
  },
  clearAllNotifications: function({ commit }) {
    notificationAPI.clearAll(() => commit("markAllRead"), e => console.error(e))
  }
}

export default {
  namespaced: true,
  state,
  getters,
  mutations,
  actions
}
