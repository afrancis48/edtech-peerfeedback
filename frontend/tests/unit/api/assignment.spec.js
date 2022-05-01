import sinon from "sinon"
import axios from "axios"
import { expect } from "chai"
import assignmentAPI from "@/api/assignment"

describe("🔌  API: assignment", function() {
  let sandbox = sinon.createSandbox()
  afterEach(() => sandbox.restore())

  const assignments = [
    { id: 1, name: "Addition" },
    { id: 2, name: "Subtraction" }
  ]

  describe("↳ getCourseAssignments()", function() {
    it("should get assignments for a given course", function(done) {
      sandbox.stub(axios, "get").resolves({ data: assignments })
      const cb = c => {
        expect(c).to.deep.equal(assignments)
        done()
      }
      assignmentAPI.getCourseAssignments(1, cb)
      sinon.assert.calledOnce(axios.get)
      sinon.assert.calledWith(axios.get, "/api/course/1/assignments/")
    })
  })

  describe("↳ getAssignment()", function() {
    it("should get one assignment specified using the id", function(done) {
      sandbox.stub(axios, "get").resolves({ data: assignments[0] })
      const cb = c => {
        expect(c).to.deep.equal(assignments[0])
        done()
      }
      assignmentAPI.getAssignment({ course_id: 1, assignment_id: 5 }, cb)
      sinon.assert.calledOnce(axios.get)
      sinon.assert.calledWith(axios.get, "/api/course/1/assignment/5/")
    })
  })

  describe("↳ getSettings()", function() {
    it("should get the requested assignment's settings", function(done) {
      const settings = { id: 2, assignment_id: 3, max_reviews: 5, rubric_id: 7 }
      sandbox.stub(axios, "get").resolves({ data: settings })
      const cb = s => {
        expect(s).to.deep.equal(settings)
        done()
      }
      assignmentAPI.getSettings({ course_id: 1, assignment_id: 3 }, cb)
      sinon.assert.calledOnce(axios.get)
      sinon.assert.calledWith(
        axios.get,
        "/api/assignment/settings/?course_id=1&assignment_id=3"
      )
    })
  })

  describe("↳ updateSettings️()", function() {
    it("should send a PUT request to the API update the settings", function(done) {
      const settings = { id: 2, assignment_id: 3, max_reviews: 5, rubric_id: 7 }
      const cb = () => done()
      sandbox.stub(axios, "put").resolves({ data: "OK" })
      assignmentAPI.updateSettings(settings, cb)
      sinon.assert.calledOnce(axios.put)
      sinon.assert.calledWith(axios.put, "/api/assignment/settings/2/")
    })
  })
})
