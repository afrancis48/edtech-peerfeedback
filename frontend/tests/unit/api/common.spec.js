import { authHead } from "@/api/common.js"
import { expect } from "chai"

describe("⛽️ utilities", function() {
  describe("authHead()", function() {
    it("should return a object with authorization headers", function() {
      let headObj = authHead("dummy token")
      expect(headObj).to.have.property("headers")
      expect(headObj.headers).to.have.property("Authorization")
      expect(headObj.headers.Authorization).to.equal("Bearer dummy token")
    })
  })
})
