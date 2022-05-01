import { expect } from "chai"
import { mutations, actions } from "@/store/modules/feedback"
import { testAction } from "../utils"
import axios from "axios"
import sinon from "sinon"

describe("🗄  Store: feedback", function() {
  describe("💉  mutations", function() {
    describe("↳ setFeedbacks()", function() {
      it("should set the store all value if payload is array", function() {
        const state = { all: [] }
        mutations.setFeedbacks(state, [1, 2, 3])
        expect(state.all).to.deep.equal([1, 2, 3])
      })
      it("should not set the all state if payload is not an array", function() {
        const state = { all: [] }
        mutations.setFeedbacks(state, "many feedbacks")
        expect(state.all).to.deep.equal([])
        mutations.setFeedbacks(state, { value: 2 })
        expect(state.all).to.deep.equal([])
      })
    })
  })

  describe("⛷  actions", function() {
    const sandbox = sinon.createSandbox()
    afterEach(function() {
      sandbox.restore()
    })

    describe("↳ getExtraFeedbackRequest()", function() {
      it("should load the extra feedback request in the store", function(done) {
        const state = { extraLoading: false, extra: {} }
        const extra = { id: 1, active: true }
        const expected = [
          { type: "setExtraLoading", payload: true },
          { type: "setExtra", payload: extra },
          { type: "setExtraLoading", payload: false }
        ]
        const ids = { course_id: 2, assignment_id: 5 }
        sandbox.stub(axios, "get").resolves({ data: extra })
        testAction(actions.getExtraFeedbackRequest, ids, state, expected, done)
      })
    })

    describe("↳ requestExtraFeedback()", function() {
      it("should request extra feedback for the user and return a promise", function(done) {
        const state = { extra: { active: false } }
        const extra = { id: 1, active: true }
        const expected = [{ type: "setExtra", payload: extra }]
        const ids = { course_id: 2, assignment_id: 5 }
        sandbox.stub(axios, "post").resolves({ data: extra })
        testAction(actions.requestExtraFeedback, ids, state, expected, done)
      })
    })
  })

  describe("⛴  getters", function() {
    it("No getters implemented yet")
  })
})
