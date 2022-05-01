import { Role, Selector } from "testcafe"
import { HOST, ADMIN_USER, ADMIN_PASS, STUDENT_PASS } from "./conf"

const loginBtn = Selector("button").withAttribute("type", "submit")
const authorizeBtn = Selector("input").withAttribute("type", "submit")
const username = Selector("#pseudonym_session_unique_id")
const password = Selector("#pseudonym_session_password")

export const teacher = Role(`${HOST}/users/login`, async t => {
  await t
    .typeText(username, ADMIN_USER)
    .typeText(password, ADMIN_PASS)
    .click(loginBtn)
    .click(authorizeBtn)
})

export const studentRole = function(loginId) {
  return Role(`${HOST}/users/login`, async t => {
    await t
      .typeText(username, loginId)
      .typeText(password, STUDENT_PASS)
      .click(loginBtn)
      .click(authorizeBtn)
  })
}
