import { expect } from "chai"
import { getters, mutations, actions } from "@/store/modules/task"
import { testAction } from "../utils"
import axios from "axios"
import sinon from "sinon"

describe("🗄  Store: task", function() {
  describe("💉  mutations", function() {
    describe("↳ setTasks()", function() {
      it("should set state tasks if payload is an array", function() {
        const state = { tasks: [] }
        const payload = [{ id: 5 }, { id: 34 }]
        mutations.setTasks(state, payload)
        expect(state.tasks).to.deep.equal(payload)
      })

      it("should not affect the state if payload is not an array", function() {
        const state = { tasks: [{ id: 34 }, { id: 45 }] }
        mutations.setTasks(state, "many new tasks")
        expect(state.tasks).to.not.equal("many new tasks")
        mutations.setTasks(state, 45)
        expect(state.tasks).to.not.equal(45)
        mutations.setTasks(state, { name: "user", profile: "hello" })
        expect(state.tasks).to.not.equal({ name: "user", profile: "hello" })
      })
    })

    describe("↳ setLoading()", function() {
      it("should set the passed value as the isLoading state", function() {
        const state = { isLoading: false }
        mutations.setLoading(state, true)
        expect(state.isLoading).to.be.true
        mutations.setLoading(state, false)
        expect(state.isLoading).to.be.false
      })

      it("should not change the state if non-boolean value is passed", function() {
        const state = { isLoading: false }
        mutations.setLoading(state, 1)
        expect(state.isLoading).to.not.equal(1)
        expect(state.isLoading).to.be.false
        mutations.setLoading(state, "true")
        expect(state.isLoading).to.not.equal("true")
        expect(state.isLoading).to.be.false
      })
    })

    describe("↳ setCurrent()", function() {
      it("should set the current task if payload is object", function() {
        const state = { current: null }
        mutations.setCurrent(state, { id: 4 })
        expect(state.current).to.deep.equal({ id: 4 })
      })

      it("should not set the current if payload is not object", function() {
        const state = { current: null }
        mutations.setCurrent(state, "task")
        expect(state.current).to.not.equal("task")
      })
    })
  })

  describe("⛷  actions", function() {
    const sandbox = sinon.createSandbox()
    afterEach(() => sandbox.restore())

    describe("↳ getTaskForSubmission()", function() {
      it("should load the task from store if ids match", function(done) {
        const state = {
          tasks: [
            {
              id: 1,
              course_id: 2,
              assignment_id: 4,
              pairing: { recipient: { id: 5 } }
            },
            {
              id: 2,
              course_id: 3,
              assignment_id: 8,
              pairing: { recipient_id: { id: 7 } }
            }
          ]
        }
        const expected = [
          { type: "clearCurrent" },
          { type: "setCurrentLoading", payload: true },
          { type: "setCurrent", payload: state.tasks[0] },
          { type: "setCurrentLoading", payload: false }
        ]
        const ids = { course_id: 2, assignment_id: 4, user_id: 5 }
        testAction(actions.getTaskForSubmission, ids, state, expected, done)
      })

      it("should load the task from the API if not present in state", function(done) {
        const task = {
          id: 4,
          course_id: 34,
          assignment_id: 45,
          pairing: { recipient_id: 3 }
        }
        const state = { tasks: [], isLoading: false, current: null }
        sandbox.stub(axios, "get").resolves({ data: task })
        const ids = { course_id: 34, assignment_id: 45, user_id: 3 }
        const expected = [
          { type: "clearCurrent" },
          { type: "setCurrentLoading", payload: true },
          { type: "setCurrent", payload: task },
          { type: "setCurrentLoading", payload: false }
        ]
        testAction(actions.getTaskForSubmission, ids, state, expected, done)
      })
    })
  })

  describe("⛴  getters", function() {
    describe("↳ incompleteTasks()", function() {
      it("should return only the tasks which are not complete", function() {
        const state = {
          tasks: [
            { status: "PENDING" },
            { status: "IN_PROGRESS" },
            { status: "COMPLETE" }
          ]
        }
        expect(getters.incompleteTasks(state)).to.have.lengthOf(2)
      })
    })
  })
})
