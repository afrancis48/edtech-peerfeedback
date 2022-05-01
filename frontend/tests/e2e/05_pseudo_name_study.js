// There needs to be a number of factors that need to be satisfied for these
// tests to pass.
// 1. Creating a Study - Manual
// 2. Enrolling of students and assignments for the study - Manual
//
// These manual steps should be automated when possible

import { studentRole, teacher } from "./roles"
import { FeedbackPage, HomePage, PairingTablePage } from "./pages"
import { HOST, STUDY_STUDENT_NUMBER } from "./conf"

let graderUsername = false
let recipientName = false
let feedbackURL = false

fixture`Pseudo Names Study`

/**
 * NOTE
 * The Grader and Recipient are chosen by searching for students with `1` in
 * their names. All the students with 1 in their name are enrolled for the study
 * during the study setup. This test might fail if the condition is not fulfilled
 * during the enrollment process.
 */
test("Determine grader and recipient; Show real name in the Pairing Table", async t => {
  const tablePage = new PairingTablePage()
  await t
    .useRole(teacher)
    .navigateTo(`${HOST}/app/course/1/assignment/2/pairing-table`)
    .click(tablePage.grdSearchBtn)
    .typeText(tablePage.gradersInput, STUDY_STUDENT_NUMBER)
    .pressKey("enter")
    .click(tablePage.recpSearchBtn)
    .typeText(tablePage.recipientInput, STUDY_STUDENT_NUMBER)
    .pressKey("enter")
    .expect(tablePage.rows.count)
    .gt(0)

  const firstRow = await tablePage.rows.nth(0)
  let graderName = await firstRow.find("td").nth(1).textContent
  let id = graderName.trim().split(" ")[1]
  id = id.length === 1 ? "0" + id : id
  graderUsername = "student00" + id + "@example.edu"

  let recipient = firstRow
    .find("td")
    .nth(2)
    .find("span.chip")
    .nth(0)
  recipientName = await recipient.textContent
  feedbackURL = await recipient.find("a").getAttribute("href")
  recipientName = recipientName.trim()
})

test("Real Name is not shown in the Task List", async t => {
  await t
    .expect(graderUsername)
    .ok()
    .expect(recipientName)
    .ok()
  const graderRole = studentRole(graderUsername)
  const homepage = new HomePage()
  await t
    .useRole(graderRole)
    .navigateTo(`${HOST}/app/dashboard/`)
    .expect(homepage.tasks.count)
    .gt(0)

  const taskCount = await homepage.tasks.count
  for (let i = 0; i < taskCount; i++) {
    await t.expect(homepage.tasks.nth(i).textContent).notContains(recipientName)
  }
})

test("Pseudo Name is shown in the feedback Page", async t => {
  await t
    .expect(graderUsername)
    .ok()
    .expect(recipientName)
    .ok()
  const graderRole = studentRole(graderUsername)
  const fbPage = new FeedbackPage()

  await t
    .useRole(graderRole)
    .navigateTo(HOST + feedbackURL)
    .expect(fbPage.submissionTitle.textContent)
    .notContains(recipientName)
})

test("Students not enrolled for study see real names in tasks", async t => {
  const tablePage = new PairingTablePage()
  let nonPartGrader

  /**
   * Step 1: Login as the admin user and pick out a non participating grader
   *         and a participating recipient
   */
  await t
    .useRole(teacher)
    .navigateTo(`${HOST}/app/course/1/assignment/2/pairing-table`)
    .click(tablePage.recpSearchBtn)
    .typeText(tablePage.recipientInput, recipientName)
    .pressKey("enter")
    .expect(tablePage.rows.count)
    .gt(0)

  const rowsCount = await tablePage.rows.count
  for (let i = 0; i < rowsCount; i++) {
    let graderName = await tablePage.rows
      .nth(i)
      .find("td")
      .nth(1).textContent
    // grader name doesn't contain 1 which means he is not enrolled for the study
    if (graderName.indexOf("1") === -1) {
      let id = graderName.trim().split(" ")[1]
      id = id.length === 1 ? "0" + id : id
      nonPartGrader = "student00" + id + "@example.edu"
      break
    }
  }

  await t.expect(nonPartGrader).ok()

  /**
   * Step 2: Log in as the identified grader and ensure recipient's real name
   *         is show in the task item
   */
  const homepage = new HomePage()
  await t
    .useRole(studentRole(nonPartGrader))
    .navigateTo(`${HOST}/app/dashboard/`)
    .expect(homepage.tasklist.textContent)
    .contains(recipientName)
})
