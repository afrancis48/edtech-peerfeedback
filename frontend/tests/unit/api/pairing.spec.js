import sinon from "sinon"
import axios from "axios"
import { expect } from "chai"
import pairingAPI from "@/api/pairing"

describe("🔌  API: pairing", function() {
  let sandbox = sinon.createSandbox()
  afterEach(() => sandbox.restore())

  describe("↳ getPairings()", function() {
    it("gets the pairings from '/api/assignment/{id}/pairs/", function(done) {
      sandbox.stub(axios, "get").resolves({ data: [] })
      const cb = pairs => {
        expect(pairs).to.deep.equal([])
        done()
      }
      pairingAPI.getPairings({ course_id: 1, assignment_id: 5 }, cb)
      sinon.assert.calledOnce(axios.get)
      sinon.assert.calledWith(axios.get, "/api/course/1/assignment/5/pairs/")
    })
  })
})
