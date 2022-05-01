import Vue from "vue"
import Vuex from "vuex"

import mutationFns from "./mutations"
import getterFns from "./getters"
import actionFns from "./actions"
import createActionQueueModerator from "./moderator"

import assignment from "./modules/assignment"
import comment from "./modules/comment"
import course from "./modules/course"
import feedback from "./modules/feedback"
import logger from "./modules/logger"
import notification from "./modules/notification"
import pairing from "./modules/pairing"
import rubric from "./modules/rubric"
import submission from "./modules/submission"
import task from "./modules/task"
import user from "./modules/user"

Vue.use(Vuex)

const actionQueue = createActionQueueModerator()
const store = new Vuex.Store({
  modules: {
    assignment,
    comment,
    course,
    feedback,
    logger,
    notification,
    pairing,
    rubric,
    submission,
    task,
    user
  },
  state: {},
  mutations: mutationFns,
  getters: getterFns,
  actions: actionFns,
  plugins: [actionQueue]
})

export default store
