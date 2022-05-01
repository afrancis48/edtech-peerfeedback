import { expect } from "chai"
import { getters, mutations, actions } from "@/store/modules/course"
import { testAction } from "../utils"
import axios from "axios"
import sinon from "sinon"

describe("🗄  Store: course", function() {
  describe("💉  mutations", function() {
    describe("↳ setCourses()", function() {
      it("sets the courses if the payload is an array", function() {
        const state = { courses: [] }
        const payload = [{ id: 1 }, { id: 4 }]
        mutations.setCourses(state, payload)
        expect(state.courses).to.deep.equal(payload)
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
        mutations.setLoading(state, [true])
        expect(state.isLoading).to.not.equal([true])
        expect(state.isLoading).to.be.false
        mutations.setLoading(state, { status: true })
        expect(state.isLoading).to.not.equal({ status: true })
        expect(state.isLoading).to.be.false
      })
    })

    describe("↳ setStudents()", function() {
      it("should set the value of students if payload is array", function() {
        const state = { students: [] }
        mutations.setStudents(state, [1, 2, 3])
        expect(state.students).to.deep.equal([1, 2, 3])
      })
      it("should not set the value of the students if not array", function() {
        const state = { students: [] }
        let payload = { value: "students" }
        mutations.setStudents(state, payload)
        expect(state.students).to.deep.not.equal(payload)
        mutations.setStudents(state, null)
        expect(state.students).to.be.not.null
      })
    })

    describe("↳ clearStudents()", function() {
      it("should set the students value to an empty array", function() {
        const state = { students: [1, 2, 3, 4] }
        mutations.clearStudents(state)
        expect(state.students).to.deep.equal([])
      })
    })

    describe("↳ clearCurrentCourse()", function() {
      it("should set the current course to null", function() {
        const state = { current: { id: 3, name: "demo course" } }
        mutations.clearCurrentCourse(state)
        expect(state.current).to.be.null
      })
    })
  })

  describe("⛷  actions", function() {
    const sandbox = sinon.createSandbox()
    afterEach(() => sandbox.restore())
    describe("↳ getCourses()", function() {
      it("gets the courses via api and updates the store", function(done) {
        const response = {
          data: [{ id: 1, name: "course 1" }, { id: 2, name: "course 2" }]
        }
        const state = { courses: [] }
        sandbox.stub(axios, "get").resolves(response)
        const expected = [
          { type: "setLoading", payload: true },
          { type: "setCourses", payload: response.data },
          { type: "setLoading", payload: false }
        ]
        testAction(actions.getCourses, null, state, expected, done)
      })
    })

    describe("↳ setCurrent()", function() {
      it("should set the course if it already exists", function(done) {
        const state = {
          courses: [{ id: 1, name: "c1" }, { id: 4, name: "c4" }]
        }
        const expected = [
          { type: "clearCurrentCourse", payload: null },
          { type: "clearStudents", payload: null },
          { type: "setCurrentCourse", payload: { id: 4, name: "c4" } }
        ]
        testAction(actions.setCurrent, 4, state, expected, done)
      })
      it("should call the API and commit the response", function(done) {
        const state = { courses: [] }
        const course = { id: 2, name: "course 2" }
        sandbox.stub(axios, "get").resolves({ data: course })
        const expected = [
          { type: "clearCurrentCourse", payload: null },
          { type: "clearStudents", payload: null },
          { type: "setLoading", payload: true },
          { type: "setCurrentCourse", payload: course },
          { type: "setLoading", payload: false }
        ]
        testAction(actions.setCurrent, 2, state, expected, done)
        sinon.assert.called(axios.get)
      })
    })

    describe("↳ setStudents()", function() {
      it("should load the students from the api", function(done) {
        const state = {
          students: []
        }
        const students = [{ id: 1, name: "Alice" }, { id: 2, name: "Bob" }]
        const expected = [{ type: "setStudents", payload: students }]
        sandbox.stub(axios, "get").resolves({ data: students })
        testAction(actions.getStudents, 1, state, expected, done)
        sinon.assert.called(axios.get)
      })
    })
  })

  describe("⛴  getters", function() {
    describe("↳ role()", function() {
      it("should return false if the current course is not set", function() {
        const state = { current: false }
        expect(getters.role(state)).to.be.false
      })
      it("should return false if there is no enrollment property to lookup", function() {
        const state = { current: { id: 2 } }
        expect(getters.role(state)).to.be.false
      })
      it("should return 'not_enrolled' if there is no enrollement", function() {
        const state = { current: { enrollments: [] } }
        expect(getters.role(state)).to.equal("not_enrolled")
      })
      it("should return the enrollment status if there is 1 enrollment", function() {
        const state = { current: { enrollments: [{ type: "student" }] } }
        expect(getters.role(state)).to.equal("student")
      })
      it("should return first enrollment for multiple enrollments", function() {
        const state = {
          current: { enrollments: [{ type: "ta" }, { type: "teacher" }] }
        }
        expect(getters.role(state)).to.equal("ta")
      })
    })
  })
})
