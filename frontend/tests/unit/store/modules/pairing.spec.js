import { expect } from "chai"
import { mutations, actions } from "@/store/modules/pairing"
import { testAction } from "../utils"
import axios from "axios"
import sinon from "sinon"

describe("🗄  Store: pairing", function() {
  describe("💉  mutations", function() {
    const state = { all: [], isLoading: false }

    describe("↳ setLoading()", function() {
      it("should set the loading value if payload is boolean", function() {
        mutations.setLoading(state, true)
        expect(state.isLoading).to.be.true
        mutations.setLoading(state, false)
        expect(state.isLoading).to.be.false
      })
      it("shouldn't change the loading value if payload is not boolean", function() {
        mutations.setLoading(state, "true")
        expect(state.isLoading).to.not.equal("true")
        expect(state.isLoading).to.be.false
        mutations.setLoading(state, 1)
        expect(state.isLoading).to.not.equal(1)
        expect(state.isLoading).to.be.false
      })
    })

    describe("↳ setAll()", function() {
      it("should set the all value if the payload is an array", function() {
        const pairs = [
          { id: 1, receiver: 23, grader: 24 },
          { id: 2, receiver: 34, grader: 24 }
        ]
        mutations.setAll(state, pairs)
        expect(state.all).to.deep.equal(pairs)
      })
      it("shouldn't change the all value if the payload is not array", function() {
        mutations.setAll(state, "new pairs")
        expect(state.all).to.not.equal("new pairs")
        mutations.setAll(state, { id: 3, receiver: 34, grader: 3 })
        expect(state.all).to.deep.not.equal({ id: 3, receiver: 34, grader: 3 })
      })
    })
  })

  describe("⛷  actions", function() {
    const sandbox = sinon.createSandbox()
    afterEach(function() {
      sandbox.restore()
    })
    describe("↳ getAssignmentPairs()", function() {
      it("should call the API and load the pairs to store", function(done) {
        const state = { all: [], isLoading: false }
        const pairs = [{ id: 1, receiver: 2, grader: 3 }]
        sandbox.stub(axios, "get").resolves({ data: pairs })
        const expected = [
          { type: "clearAll" },
          { type: "setLoading", payload: true },
          { type: "setAll", payload: pairs },
          { type: "setLoading", payload: false }
        ]
        testAction(actions.getAssignmentPairs, 3, state, expected, done)
      })
    })
  })

  describe("⛴  getters", function() {
    it("No getters implemented yet")
  })
})
