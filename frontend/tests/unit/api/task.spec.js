import sinon from "sinon"
import axios from "axios"
import { expect } from "chai"
import taskAPI from "@/api/task"

describe("🔌  API: task", function() {
  let sandbox = sinon.createSandbox()
  afterEach(() => sandbox.restore())

  describe("↳ getSubmissionTask()", function() {
    it("should get the tasks from the api server", function(done) {
      const task = { id: 1, state: "PENDING" }
      sandbox.stub(axios, "get").resolves({ data: task })
      const ids = { course_id: 2, assignment_id: 4, user_id: 34 }
      const cb = t => {
        expect(t).to.deep.equal(task)
        done()
      }

      taskAPI.getSubmissionTask(ids, cb)
      sinon.assert.calledOnce(axios.get)
      sinon.assert.calledWith(
        axios.get,
        "/api/course/2/assignment/4/user/34/task/"
      )
    })
  })
})
