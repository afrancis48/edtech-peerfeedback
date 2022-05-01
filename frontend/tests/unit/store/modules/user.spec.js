import { expect } from "chai"
import { actions, mutations, getters } from "@/store/modules/user"
import { testAction } from "../utils"
import axios from "axios"
import sinon from "sinon"

// Storage Mock
const storageMock = {
  storage: {},
  setItem: function(key, value) {
    this.storage[key] = value || ""
  },
  getItem: function(key) {
    return key in this.storage ? this.storage[key] : null
  },
  removeItem: function(key) {
    delete this.storage[key]
  },
  get length() {
    return Object.keys(this.storage).length
  },
  key: function(i) {
    var keys = Object.keys(this.storage)
    return keys[i] || null
  }
}
global.localStorage = storageMock

describe("🗄  Store: user", function() {
  describe("💉  mutations", function() {
    describe("↳ setTokens()", function() {
      let state = {}
      beforeEach(function() {
        state.accessToken = ""
        state.refreshToken = ""
      })
      it("stores the accessToken and the refreshToken to the store", function() {
        const payload = {
          access_token: "dummy access",
          refresh_token: "dummy refresh"
        }
        mutations.setTokens(state, payload)
        expect(state.accessToken).to.equal("dummy access")
        expect(state.refreshToken).to.equal("dummy refresh")
      })
      it("should store empty strings if the payload is empty", function() {
        mutations.setTokens(state)
        expect(state.accessToken).to.equal("")
        expect(state.refreshToken).to.equal("")
      })
    })

    describe("↳ clearTokens()", function() {
      const state = {
        accessToken: "some token",
        refreshToken: "refresh token"
      }
      it("should set the access and refresh token to an empty string", function() {
        mutations.clearTokens(state)
        expect(state.accessToken).to.be.empty
        expect(state.refreshToken).to.be.empty
      })
      it("removes the refresh token from the local storage", function() {
        sinon.stub(localStorage, "removeItem")
        mutations.clearTokens(state)
        expect(localStorage.removeItem.called).to.be.true
      })
    })
  })

  describe("⛷  actions", function() {
    describe("↳ logout()", function() {
      it("should call the logout api and clear the tokens", function(done) {
        const response = { data: "OK" }
        sinon.stub(axios, "post").resolves(response)
        const state = {
          accessToken: "test access token",
          refreshToken: "test refresh token"
        }
        const expected = [{ type: "clearTokens" }]
        testAction(actions.logout, null, state, expected, done)
      })
    })
  })

  describe("⛴  getters", function() {
    describe("↳ isLoggedIn()", function() {
      it("returns true if the access token is set in the store", function() {
        const state = { accessToken: "dummy" }
        expect(getters.isLoggedIn(state)).to.be.true
      })
      it("returns false if the accesstoken is empty or null", function() {
        let state = { accessToken: "" }
        expect(getters.isLoggedIn(state)).to.be.false

        state.accessToken = null
        expect(getters.isLoggedIn(state)).to.be.false
      })
    })

    describe("↳ hasRefreshToken()", function() {
      it("returns true if the refresh token is present in the store", function() {
        const state = { refreshToken: "dummy" }
        expect(getters.hasRefreshToken(state)).to.be.true
      })
      it("returns false if the refresh token is empty or null", function() {
        let state = { refreshToken: "" }
        expect(getters.hasRefreshToken(state)).to.be.false

        state.refreshToken = null
        expect(getters.hasRefreshToken(state)).to.be.false
      })
    })
  })
})
