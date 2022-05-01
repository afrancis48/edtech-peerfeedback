import { ClientFunction } from "testcafe"
import { teacher } from "./roles"
import { SettingsPage, RubricCreatorPage } from "./pages"
import { HOST } from "./conf"

fixture`Rubric Management`

const getPageUrl = ClientFunction(() => window.location.href)
const settingsPage = new SettingsPage()
const rubricCreator = new RubricCreatorPage()

test("Create Rubric", async t => {
  await t
    // 1. Teacher logs in and goes to the assignment settings
    .useRole(teacher)
    .navigateTo(`${HOST}/app/course/1/assignment/2/settings`)
    // 2. The user sees there is no rubric available set
    .expect(settingsPage.useRubricCheckBox.checked)
    .notOk()
    // and that the rubric selection is disabled
    .expect(settingsPage.rubricSelect.hasAttribute("disabled"))
    .ok()
    // 3. The user switches on the `User rubric for assignment` option
    .click(settingsPage.useRubricCheckBox)
    // 4. Now the option is set and the rubric selection is enabled
    .expect(settingsPage.useRubricCheckBox.checked)
    .ok()
    .expect(settingsPage.rubricSelect.hasAttribute("disabled"))
    .notOk()
    // 5. The user clicks the rubric select and chooses the "Create" option
    .click(settingsPage.rubricSelect)
    .click(settingsPage.creatorOption)
    // 6. The user is sent to the rubric creator
    .expect(getPageUrl())
    .contains("/app/rubric/creator")
    // 7. Type in the rubric name and descripton
    .typeText(rubricCreator.rubricNameInput, "E2E Test Rubric")
    .typeText(
      rubricCreator.rubricDescription,
      "A rubric created for End to End testing"
    )
    // 8. User adds a criteria by clicking the Add Criteria button
    .click(rubricCreator.addCriteriaBtn)
    // 9. Input the the details about the criteria
    .typeText(rubricCreator.cZeroName, "Quality", { replace: true })
    .typeText(rubricCreator.cZeroDesc, "Quality of the work submitted")
    // 10. Add some levels for the criteria
    .click(rubricCreator.cZeroAddLvlBtn)
    .click(rubricCreator.cZeroAddLvlBtn)
    // 11. Enter the details for the different levels
    .typeText(rubricCreator.levelZero.find("input").nth(0), "10", {
      replace: true
    })
    .typeText(rubricCreator.levelZero.find("textarea").nth(0), "Excellent")
    .typeText(rubricCreator.levelOne.find("input").nth(0), "5")
    .typeText(rubricCreator.levelOne.find("textarea").nth(0), "Good")
    .typeText(rubricCreator.levelTwo.find("input").nth(0), "0")
    .typeText(rubricCreator.levelTwo.find("textarea").nth(0), "Poor")
    // 12. Assert that the total points is as per the input
    .expect(
      rubricCreator.vRubricCreator.getVue(
        ({ computed }) => computed.totalPoints
      )
    )
    .eql(10)
    // 12. Click the create rubric button
    .click(rubricCreator.createRubricBtn)
    // 13. The user is returned to the settings page
    .expect(getPageUrl())
    .contains("/app/course/1/assignment/2/settings", {
      timeout: 10000
    })
})

test("Set rubric for an assignment", async t => {
  await t
    // 1. Login as the teacher
    .useRole(teacher)
    .navigateTo(`${HOST}/app/course/1/assignment/2/settings`)
    // 2. The user sees there is no rubric available set
    .expect(settingsPage.useRubricCheckBox.checked)
    .notOk()
    // and that the rubric selection is disabled
    .expect(settingsPage.rubricSelect.hasAttribute("disabled"))
    .ok()
    // 3. The user switches on the `User rubric for assignment` option
    .click(settingsPage.useRubricCheckBox)
    // 4. Now the option is set and the rubric selection is enabled
    .expect(settingsPage.useRubricCheckBox.checked)
    .ok()
    .expect(settingsPage.rubricSelect.hasAttribute("disabled"))
    .notOk()
    // 5. The user clicks the rubric select and chooses the rubric
    .click(settingsPage.rubricSelect)
    .click(settingsPage.testRubric)
    // 6. And saves the settings of the assignment
    .click(settingsPage.saveBtn)
    .expect(settingsPage.savedToast.visible)
    .ok()
})
