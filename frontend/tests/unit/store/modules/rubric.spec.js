import { expect } from "chai"
import { mutations, actions } from "@/store/modules/rubric"
import { testAction } from "../utils"
import axios from "axios"
import sinon from "sinon"

describe("🗄  Store: rubric", function() {
  describe("💉  mutations", function() {
    describe("↳ setAll()", function() {
      const state = { all: [] }
      it("should set the all value if the payload is an array", function() {
        mutations.setAll(state, [1, 2, 3])
        expect(state.all).to.deep.equal([1, 2, 3])
      })
      it("shouldn't change the all value if the payload isn't an array", function() {
        mutations.setAll(state, { value: [1, 2, 3] })
        expect(state.all).to.deep.not.equal({ value: [1, 2, 3] })
        mutations.setAll(state, "some rubrics")
        expect(state.all).to.not.equal("some rubrics")
      })
    })

    describe("↳ setLoading()", function() {
      const state = { isLoading: false }
      it("should set the value of isLoading if bool", function() {
        mutations.setLoading(state, true)
        expect(state.isLoading).to.be.true
        mutations.setLoading(state, false)
        expect(state.isLoading).to.be.false
      })
      it("shouldn't set the value of isLoading if not bool", function() {
        mutations.setLoading(state, "true")
        expect(state.isLoading).to.not.equal("true")
        expect(state.isLoading).to.be.not.true
      })
    })
  })

  describe("⛷  actions", function() {
    const sandbox = sinon.createSandbox()
    afterEach(function() {
      sandbox.restore()
    })
    describe("↳ getAllRubrics()", function() {
      it("should get the rubrics from api and load it into the store", function(done) {
        const state = { all: [], isLoading: false }
        const rubrics = [
          { id: 1, name: "rubric 1" },
          { id: 2, name: "rubric 2" }
        ]
        sandbox.stub(axios, "get").resolves({ data: rubrics })
        const expected = [
          { type: "setLoading", payload: true },
          { type: "setAll", payload: rubrics },
          { type: "setLoading", payload: false }
        ]
        testAction(actions.getAllRubrics, null, state, expected, done)
      })
    })
  })

  describe("⛴  getters", function() {
    it("Not implemented yet")
  })
})
