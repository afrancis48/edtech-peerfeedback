import { Selector, ClientFunction } from "testcafe"
import { teacher } from "./roles"
import { PairingPage, PairingTablePage } from "./pages"
import { HOST } from "./conf"

fixture`Pairing`

const getPageUrl = ClientFunction(() => window.location.href)
const page = new PairingPage()
const tablePage = new PairingTablePage()

test("CSV Pairing", async t => {
  await t
    // confirm any rubric warnings
    .setNativeDialogHandler(() => true)
    // 1. The user logs in as the teacher
    .useRole(teacher)
    .navigateTo(`${HOST}/app/course/1/assignment/1/pair/`)
    // 2. the user clicks the CSV tab
    .click(page.csvTabBtn)
    // 3. notices that the pairing button is disabled
    .expect(page.csvPairBtn.getAttribute("disabled"))
    .ok()
    // 4. enters the emails of the students to be paired
    .typeText(
      page.csvInput,
      "student0010@example.edu, student0001@example.edu, student0002@example.edu"
    )
    // 5. Now the pairing button is enabled
    .expect(page.csvPairBtn.hasAttribute("disabled"))
    .notOk()
    // 6. the user clicks the pair button
    .click(page.csvPairBtn)
    // 7. a progress bar appears to show the progress
    .expect(page.vProgress.visible)
    .ok()
    // 8. Once the pairing is complete, user is redirected to the pairing table
    .expect(getPageUrl())
    .contains("pairing-table", { timeout: 60000 })
    // 9. In the pairing table ensure the pairing has actually happened
    .expect(tablePage.studentRow("Student 10").textContent)
    .contains("Student 1")
})

test("Manual Pairing", async t => {
  await t
    // confirm any rubric warnings
    .setNativeDialogHandler(() => true)
    // 1. login as the teacher
    .useRole(teacher)
    .navigateTo(`${HOST}/app/course/1/assignment/1/pair/`)
    // 2. the user switches to the manual pairing tab
    .click(page.manualTabBtn)
    // 3. notices that the pairing button is disabled
    .expect(page.manualPairBtn.getAttribute("disabled"))
    .ok()
    // 4. user searches and selects the grader from drop down
    .wait(3000) // wait until the student list is loaded
    .typeText(page.graderInput, "10")
    .click(Selector(".menu-item").withText("Student 10"))
    // 6. the users searches and selects the recipient
    .typeText(page.recipientInput, "20")
    .click(Selector(".menu-item").withText("Student 20"))
    // 7. Now the pair button is enabled
    .expect(page.manualPairBtn.getAttribute("disabled"))
    .notOk()
    // 8. the user clicks the pair button
    .click(page.manualPairBtn)
    // 8. Once the pairing is complete, user is redirected to the pairing table
    .expect(getPageUrl())
    .contains("pairing-table", { timeout: 30000 })
    // 9. In the pairing table ensure the pairing has actually happened
    .expect(tablePage.studentRow("Student 10").textContent)
    .contains("Student 20")
})

/*
    Automated pairing is done with the 2nd assignment which has a rubric setup
    so that the rubric based feedback tests could be implemented

 */
test("Automatic Pairing", async t => {
  await t
    // confirm any rubric warnings
    .setNativeDialogHandler(() => true)
    // 1. The user logs in as the teacher
    .useRole(teacher)
    .navigateTo(`${HOST}/app/course/1/assignment/2/pair`)
    // 2. The user clicks the automatic pairing tab
    .click(page.autoTabBtn)
    // 3. But the pairing button is disabled
    .expect(page.manualPairBtn.getAttribute("disabled"))
    .ok()
    // 4. The user types in the no.of pairing rounds
    .typeText(page.autoRoundsInput, "2")
    // that sets the vue data "reviewRounds"
    .expect(page.vAutoTab.getVue(({ state }) => state.reviewRounds))
    .eql(2)
    // 5. With the data entered, the pairing button gets enabled
    .expect(page.autoPairBtn.getAttribute("disabled"))
    .notOk()
    // 6. The user clicks the user button
    .click(page.autoPairBtn)
    // 7. A confirmation modal explaining the pairing is shown
    .expect(page.autoConfirmModal.visible)
    .ok()
    // 8. The user confirms the pairing to be done
    .click(page.autoConfirmBtn)
    // 9. A progressbar showing the background pairing process is shown
    .expect(page.vProgress.visible)
    .ok()
    // 10. While the pairing process is complete the user is redirected to
    // the pairing table to see newly created pairs
    .expect(getPageUrl())
    .contains("pairing-table", { timeout: 180000 })
})
