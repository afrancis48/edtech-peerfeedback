import sinon from "sinon"
import axios from "axios"
import { expect } from "chai"
import feedbackAPI from "@/api/feedback"

describe("🔌  API: feedback", function() {
  let sandbox = sinon.createSandbox()
  afterEach(() => sandbox.restore())

  describe("↳ getExtraFeedback()", function() {
    it("should get the user's extra feedback request from the api", function(done) {
      const extra = { id: 3, active: true, assignment_id: 3 }
      const cb = e => {
        expect(e).to.deep.equal(extra)
        done()
      }
      sandbox.stub(axios, "get").resolves({ data: extra })
      feedbackAPI.getExtraFeedback(2, 3, cb)
      sinon.assert.calledWith(
        axios.get,
        "/api/extra_feedback/?course_id=2&assignment_id=3"
      )
    })
  })

  describe("↳ requestExtraFeedback()", function() {
    it("should send a post request create a extra_feedback", function(done) {
      const cb = e => {
        expect(e).to.equal("OK")
        done()
      }
      sandbox.stub(axios, "post").resolves({ data: "OK" })
      feedbackAPI.requestExtraFeedback({ course_id: 3, assignment_id: 2 }, cb)
      sinon.assert.calledWith(axios.post, "/api/extra_feedback/", {
        course_id: 3,
        assignment_id: 2
      })
    })
  })
})
