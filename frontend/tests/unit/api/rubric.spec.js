import sinon from "sinon"
import axios from "axios"
import { expect } from "chai"
import rubricAPI from "@/api/rubric"

describe("🔌  API: rubric", function() {
  let sandbox = sinon.createSandbox()
  afterEach(() => sandbox.restore())

  describe("↳ getRubrics()", function() {
    it("should get the rubrics from '/api/rubrics'", function() {
      const rubrics = [{ id: 1, name: "rubric 1" }, { id: 2, name: "rubric 2" }]
      sandbox.stub(axios, "get").resolves({ data: rubrics })
      const cb = r => {
        expect(r).to.deep.equal(rubrics)
      }
      rubricAPI.getRubrics(cb)
      sinon.assert.calledWith(axios.get, "/api/rubrics/")
    })
  })
})
