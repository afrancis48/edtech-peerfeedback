import { Selector, ClientFunction } from "testcafe"
import { teacher } from "./roles"
import { SettingsPage } from "./pages"
import { HOST, ADMIN_PASS, ADMIN_USER } from "./conf"

fixture`Login`.page`${HOST}/app/home`

//Returns the URL of the current web page
const getPageUrl = ClientFunction(() => window.location.href)

test("Login to Canvas", async t => {
  const canvasLoginBtn = Selector("button").withAttribute("type", "submit")
  const canvasAuthBtn = Selector("input").withAttribute("value", "Authorise")

  await t
    .click("#login")
    .typeText("#pseudonym_session_unique_id", ADMIN_USER)
    .typeText("#pseudonym_session_password", ADMIN_PASS)
    .click(canvasLoginBtn)
    .expect(getPageUrl())
    .contains("oauth2/confirm")
    .click(canvasAuthBtn)
})

fixture.skip`Initialize Course`.page`${HOST}/app/course/1/assignment/2/settings`

test("Initialize Course", async t => {
  const settingsPage = new SettingsPage()

  await t
    // 1. Login as the teacher
    .useRole(teacher)
    // 2. The Init course button is there. The user clicks the init course button
    .click(settingsPage.initCourseBtn)
    // 3. The progress bar is show when the course is initialized
    .expect(settingsPage.vProgress.visible)
    .ok()
    .wait(15000)
    // 4. Once the initialization is complete the actual settings page is loaded
    .expect(settingsPage.successToast.visible)
    .ok()
})
