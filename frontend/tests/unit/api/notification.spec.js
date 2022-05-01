import sinon from "sinon"
import axios from "axios"
import { expect } from "chai"
import noteAPI from "@/api/notification"

describe("🔌  API: notification", function() {
  const notifications = [{ id: 1, read: true }, { id: 2, read: false }]
  let sandbox = sinon.createSandbox()
  afterEach(() => sandbox.restore())

  describe("↳ getAllCourses()", function() {
    it("should get notifications from /api/notifications", function(done) {
      sandbox.stub(axios, "get").resolves({ data: notifications })
      const cb = notes => {
        expect(notes).to.deep.equal(notifications)
        done()
      }
      noteAPI.getAll(cb)
      sinon.assert.calledOnce(axios.get)
      sinon.assert.calledWith(axios.get, "/api/notifications/")
    })
  })

  describe("↳ markAsRead()", function() {
    it("should make a put request with to update read status", function(done) {
      sandbox.stub(axios, "put").resolves({ data: { id: 2, read: true } })
      const cb = note => {
        expect(note).to.deep.equal({ id: 2, read: true })
        done()
      }
      noteAPI.markAsRead(notifications[1], cb, cb)
      sinon.assert.calledOnce(axios.put)
      sinon.assert.calledWith(axios.put, "/api/notification/2/", { read: true })
    })
  })
})
