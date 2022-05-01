import { expect } from "chai"
import sinon from "sinon"
import axios from "axios"
import user from "@/api/user"

describe("🔌  API: user", function() {
  let sandbox = sinon.createSandbox()

  describe("refreshLogin()", function() {
    before(function() {
      sandbox.stub(axios, "post").resolves({ access_token: "dummy token" })
    })
    after(function() {
      sandbox.restore()
    })

    it("should make a post call with refresh token", function() {
      axios.defaults.headers.common["Authorization"] = "Bearer ACCESS_TOKEN"
      user.refreshLogin("refresh token", () => {}, () => {})
      sandbox.assert.calledOnce(axios.post)
      let thirdArg = axios.post.getCall(0).args[2]
      expect(thirdArg.headers.Authorization).to.equal("Bearer refresh token")
    })
  })

  describe("logout()", function() {
    before(function() {
      sandbox.stub(axios, "post").resolves("OK")
    })
    after(function() {
      sandbox.restore()
    })
    it("should make a post to logout", function() {
      user.logout(() => {}, () => {})
      sandbox.assert.calledOnce(axios.post)
    })
  })
})
