import { expect } from "chai"
import { getters, mutations, actions } from "@/store/modules/notification"
import { testAction } from "../utils"
import axios from "axios"
import sinon from "sinon"

describe("🗄  Store: notifications", function() {
  describe("💉  mutations", function() {
    describe("↳ setAll()", function() {
      it("saves the payload in state", function() {
        const state = { notifications: [] }
        mutations.setAll(state, [1, 2, 3])
        expect(state.notifications).to.deep.equal([1, 2, 3])
      })
      it("doesn't change the state if it payload is not an array", function() {
        const state = { notifications: [1, 2, 3] }
        mutations.setAll(state, "no notifications")
        expect(state.notifications).to.deep.equal([1, 2, 3])
      })
    })
  })

  describe("⛷  actions", function() {
    const sandbox = sinon.createSandbox()
    afterEach(() => sandbox.restore())
    describe("↳ getNotifications()", function() {
      it("should call the api and commit the notifications to state", function(done) {
        const response = {
          data: [{ id: 1, read: true }, { id: 5, read: false }]
        }
        const state = { notifications: [] }
        sandbox.stub(axios, "get").resolves(response)
        testAction(
          actions.getNotifications,
          null,
          state,
          [{ type: "setAll", payload: response.data }],
          done
        )
      })
    })

    describe("↳ markNotificationRead()", function() {
      it("should call the api and update the store on success", function(done) {
        const response = { data: { id: 2, read: true } }
        const state = { notifications: [{ id: 2, read: false }] }
        sinon.stub(axios, "put").resolves(response)
        const exMutations = [
          { type: "updateNotification", payload: response.data }
        ]
        testAction(actions.markNotificationRead, 2, state, exMutations, done)
      })
    })
  })

  describe("⛴  getters", function() {
    const state = {
      notifications: [
        { id: 1, read: true },
        { id: 2, read: true },
        { id: 3, read: true },
        { id: 4, read: false },
        { id: 5, read: false }
      ]
    }
    describe("↳ allNotifications()", function() {
      it("returns all the notifications in the store", function() {
        let all = getters.allNotifications(state)
        expect(all).to.deep.equal(state.notifications)
      })
    })
    describe("↳ readNotifications()", function() {
      it("returns only the read notifications", function() {
        let read = getters.readNotifications(state)
        expect(read.length).to.equal(3)
      })
    })
    describe("↳ unreadNotifications()", function() {
      it("returns only the unread notifications", function() {
        let unread = getters.unreadNotifications(state)
        expect(unread.length).to.equal(2)
      })
    })
  })
})
