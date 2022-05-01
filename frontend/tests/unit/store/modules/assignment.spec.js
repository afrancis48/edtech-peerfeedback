import { expect } from "chai"
import { mutations, actions } from "@/store/modules/assignment"
import { testAction } from "../utils"
import axios from "axios"
import sinon from "sinon"

describe("🗄  Store: assignment", function() {
  describe("💉 mutations", function() {
    describe("↳ setLoading()", function() {
      it("should set the loading value if boolean", function() {
        const state = { isLoading: false }
        mutations.setLoading(state, true)
        expect(state.isLoading).to.be.true
        mutations.setLoading(state, false)
        expect(state.isLoading).to.be.false
      })
      it("should not set the loading value for any other types", function() {
        const state = { isLoading: false }
        mutations.setLoading(state, 1)
        expect(state.isLoading).to.be.false
        mutations.setLoading(state, "true")
        expect(state.isLoading).to.be.false
        mutations.setLoading(state, { state: true })
        expect(state.isLoading).to.be.false
      })
    })

    describe("↳ setAssignments()", function() {
      it("should set assignments if the payload is an array", function() {
        const state = { all: [] }
        const payload = [
          { id: 1, name: "Addition" },
          { id: 2, name: "Subtraction" }
        ]
        mutations.setAssignments(state, payload)
        expect(state.all).to.deep.equal(payload)
      })
    })

    describe("↳ setCurrentAssignment()", function() {
      const state = { current: {} }
      it("should set the current value using payload", function() {
        const assignment = { id: 3, name: "Write Poem" }
        mutations.setCurrentAssignment(state, assignment)
        expect(state.current).to.deep.equal(assignment)
      })
      it("shouldn't change the current if payload isn't object", function() {
        mutations.setCurrentAssignment(state, "new assignment")
        expect(state.current).to.not.equal("new assignment")
        const fn = () => {}
        mutations.setCurrentAssignment(state, fn)
        expect(state.current).to.not.equal(fn)
      })
    })

    describe("↳ setSettings()", function() {
      const state = { settings: {} }
      it("should set the settings value if payload is an object", function() {
        const setting = { id: 3, canvas_id: 5, use_rubric: true }
        mutations.setSettings(state, setting)
        expect(state.settings).to.deep.equal(setting)
      })
    })

    describe("↳ setSettingsLoading()", function() {
      const state = { settingsLoading: false }
      it("should set the settingsLoading value is payload is bool", function() {
        mutations.setSettingsLoading(state, true)
        expect(state.settingsLoading).to.be.true
        mutations.setSettingsLoading(state, false)
        expect(state.settingsLoading).to.be.false
      })
    })
  })

  describe("⛷  actions", function() {
    const sandbox = sinon.createSandbox()
    afterEach(() => sandbox.restore())

    describe("↳ getAssignmentsInCourse()", function() {
      it("should get the assignments of given course", function(done) {
        const assigns = [
          { id: 1, name: "Addition" },
          { id: 2, name: "Subtraction" }
        ]
        const state = { all: [] }
        sandbox.stub(axios, "get").resolves({ data: assigns })
        const expected = [
          { type: "setLoading", payload: true },
          { type: "setAssignments", payload: assigns },
          { type: "setLoading", payload: false }
        ]
        testAction(actions.getAssignmentsInCourse, 5, state, expected, done)
      })
    })

    describe("↳ setCurrent()", function() {
      it("should set the current from the all array if present", function() {
        const state = {
          all: [{ id: 1, name: "Demo Assignment" }],
          current: {}
        }
        const commit = (type, payload) => {
          expect(type).to.equal("setCurrentAssignment")
          expect(payload).to.deep.equal(state.all[0])
        }
        const ids = { course_id: 1, assignment_id: 1 }
        actions.setCurrent({ commit, state }, ids)
      })

      it("should query the API and set the current assignment if not present", function(done) {
        const state = { all: [], current: {} }
        const assignment = { id: 3, name: "Demo Assignment" }
        sandbox.stub(axios, "get").resolves({ data: assignment })
        const expected = [
          { type: "setLoading", payload: true },
          { type: "setCurrentAssignment", payload: assignment },
          { type: "setLoading", payload: false }
        ]
        const ids = { course_id: 1, assignment_id: 3 }
        testAction(actions.setCurrent, ids, state, expected, done)
      })
    })

    describe("↳ updateSettings()", function() {
      const state = { settings: { id: 3, canvas_id: 4, assignment_id: 5 } }
      it("should call the API and update the server and returns a promise", function() {
        sandbox.stub(axios, "put").resolves({ data: "OK" })
        const commit = (type, payload) => {
          expect(type).to.equal("setSettings")
          expect(payload).to.equal("OK")
        }
        const updater = actions.updateSettings({ state, commit })
        expect(typeof updater.then).to.equal("function")
        sinon.assert.calledOnce(axios.put)
      })
    })
  })

  describe("⛴  getters", function() {
    it("No Getters Implemented")
  })
})
