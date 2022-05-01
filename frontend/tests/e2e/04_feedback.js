import { ClientFunction } from "testcafe"
import { studentRole } from "./roles"
import { HomePage, FeedbackPage } from "./pages"
import { HOST } from "./conf"

fixture`Student Feedback`

const getPageUrl = ClientFunction(() => window.location.href)
const homepage = new HomePage()
const feedbackPage = new FeedbackPage()
const fbText = `
Lorem Ipsum is simply dummy text of the printing and typesetting industry.
Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, 
when an unknown printer took a galley of type and scrambled it to make a type 
specimen book. It has survived not only five centuries, but also the leap into 
electronic typesetting, remaining essentially unchanged. 
`
const student10 = studentRole("student0010@example.edu")

test("Give feedback without any rubric", async t => {
  await t
    // 1. Login as a student
    .useRole(student10)
    .navigateTo(`${HOST}/app/dashboard/`)
    // 2. there is at least one task for the user to give feedback
    .expect(homepage.tasks.count)
    .gt(0)
    // 3. the user clicks on the give feedback button of a task
    .click(homepage.firstTaskBtn)
    // 4. the user is taken to the feedback page
    .expect(getPageUrl())
    .contains("/app/feedback/course/")
    // 5. The user enters the feedback in the feedback box
    .typeText(feedbackPage.fbInput, fbText)
    // 6. the user clicks the submit feedback button
    .click(feedbackPage.fbReadyBtn)
    // 7. the user clicks the confirm feedback button
    .click(feedbackPage.fbConfirmBtn)
    // 8. The feedback is posted and the feedback discussion and comment section
    //    are shown to the student
    .expect(feedbackPage.vDiscussion.visible)
    .ok()
})

test("Time tracking for read and write times", async t => {
  await t
    // 1. Login as a student
    .useRole(student10)
    .navigateTo(`${HOST}/app/dashboard/`)
    // 2. Open an available task
    .expect(homepage.tasks.count)
    .gt(0)
    .click(homepage.firstTaskBtn)
    // 3. Click on the submission content and wait for some time
    .click(feedbackPage.submission)
    .wait(10000)
    // 4. Select the feedback input and type in the feedback
    .click(feedbackPage.fbInput)
    .typeText(feedbackPage.fbInput, fbText, { speed: 0.1 })
    // 5. Submit the feedback
    .click(feedbackPage.fbReadyBtn)
    .click(feedbackPage.fbConfirmBtn)
    // 6. Assert that the read and write times match the wait times
    .expect(feedbackPage.s10fbItem.visible)
    .ok()
    .expect(
      feedbackPage.s10fbItem.getVue(({ props }) => props.feedback.read_time)
    )
    .within(9, 12)
    .expect(
      feedbackPage.s10fbItem.getVue(({ props }) => props.feedback.write_time)
    )
    .gt(50)
})

test("Submit feedback with a rubric", async t => {
  await t
    //  1. Login as a student
    .useRole(studentRole("student0005@example.edu"))
    .navigateTo(`${HOST}/app/dashboard/`)
    // 2. Open an available task
    .expect(homepage.tasks.count)
    .gt(0)
    .click(homepage.firstTaskBtn)
    // 3. Input the feedback in the input box
    .typeText(feedbackPage.fbInput, fbText)
    // 4. Choose a level on the rubric
    .click(feedbackPage.goodLevel)
    // 5. Submit the feedback
    .click(feedbackPage.fbReadyBtn)
    .click(feedbackPage.fbConfirmBtn)
    // 6. The feedback is posted and the feedback discussion and comment section
    //    are shown to the student
    .expect(feedbackPage.vDiscussion.visible)
    .ok()
})
