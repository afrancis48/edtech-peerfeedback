import sinon from "sinon"
import axios from "axios"
import { expect } from "chai"
import courseAPI from "@/api/course"

describe("🔌  API: course", function() {
  let sandbox = sinon.createSandbox()
  afterEach(() => sandbox.restore())

  const courses = [{ id: 1, name: "course 1" }, { id: 2, name: "course 2" }]
  describe("↳ getAllCourses()", function() {
    it("should get courses from /api/courses/", function(done) {
      sandbox.stub(axios, "get").resolves({ data: courses })
      const cb = c => {
        expect(c).to.deep.equal(courses)
        done()
      }
      courseAPI.getAllCourses(cb)
      sinon.assert.calledOnce(axios.get)
      sinon.assert.calledWith(axios.get, "/api/courses/")
    })
  })

  describe("↳ getCourse()", function() {
    it("should get the one course requested", function(done) {
      sandbox.stub(axios, "get").resolves({ data: courses[0] })
      const cb = c => {
        expect(c).to.deep.equal(courses[0])
        done()
      }
      courseAPI.getCourse(1, cb)
      sinon.assert.calledOnce(axios.get)
      sinon.assert.calledWith(axios.get, "/api/course/1/")
    })
  })

  describe("↳ getStudents()", function() {
    it("should get the students for the course specified", function(done) {
      let students = ["Bob", "Alice", "Cad"]
      sandbox.stub(axios, "get").resolves({ data: students })
      const cb = s => {
        expect(s).to.deep.equal(students)
        done()
      }
      courseAPI.getStudents(3, cb)
      sinon.assert.calledOnce(axios.get)
      sinon.assert.calledWith(axios.get, "/api/course/3/students/")
    })
  })
})
