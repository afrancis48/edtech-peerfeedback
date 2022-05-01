import { Selector } from "testcafe"
import VueSelector from "testcafe-vue-selectors"

export class CanvasPage {
  constructor() {}
}

/******************************************************************************
 *                   Teacher Assignment pages                                 *
 ******************************************************************************/
export class PairingPage {
  constructor() {
    this.csvPairBtn = Selector("button").withAttribute(
      "data-test",
      "csv-pair-btn"
    )
    this.manualPairBtn = Selector("button").withAttribute(
      "data-test",
      "manual-pair-btn"
    )
    this.autoPairBtn = Selector("button").withAttribute(
      "data-test",
      "auto-pair-btn"
    )
    this.csvInput = Selector("#bulkPairGrader")
    this.graderInput = Selector("#graderEmail").find("input")
    this.recipientInput = Selector("#recipientEmail").find("input")
    this.autoRoundsInput = Selector("input").withAttribute(
      "data-test",
      "pairs-input"
    )
    this.vProgress = VueSelector("ProgressBar")
    this.vAutoTab = VueSelector("AutomaticPairingTab")
    this.csvTabBtn = Selector("a")
      .withAttribute("role", "tab")
      .withText("CSV")
    this.manualTabBtn = Selector("a")
      .withAttribute("role", "tab")
      .withText("Manual")
    this.autoTabBtn = Selector("a")
      .withAttribute("role", "tab")
      .withText("Automatic")
    this.autoConfirmModal = Selector("#autopair-confirm-modal")
    this.autoConfirmBtn = Selector("button").withAttribute(
      "data-test",
      "pair-confirm-btn"
    )
  }
}

export class PairingTablePage {
  constructor() {
    this.table = Selector("#pairing-table")
    this.grdSearchBtn = this.table
      .find(".header-wrapper")
      .nth(0)
      .find(".btn-link")
    this.recpSearchBtn = this.table
      .find(".header-wrapper")
      .nth(1)
      .find(".btn-link")
    this.gradersInput = this.table
      .find("input")
      .withAttribute("title", "Search Graders")
    this.recipientInput = this.table
      .find("input")
      .withAttribute("title", "Search Recipients")
    this.rows = this.table.find("tbody").find("tr")
    this.vTable = VueSelector("AssignmentPairingTable")
  }

  studentRow(studentName) {
    return this.table
      .child("tbody")
      .child("tr")
      .withText(studentName)
  }
}

export class SettingsPage {
  constructor() {
    this.useRubricCheckBox = Selector("input").withAttribute(
      "data-test",
      "use-rubric"
    )
    this.rubricSelect = Selector("#rubric")
    this.creatorOption = this.rubricSelect
      .find("option")
      .withAttribute("value", "creator")
    this.testRubric = this.rubricSelect.find("option").withText("E2E Test")
    this.saveBtn = Selector("button").withAttribute("data-test", "save-button")
    this.savedToast = Selector(".toasted").withText("Settings saved.")
    this.initCourseBtn = Selector("button").withAttribute(
      "data-test",
      "initialize-course"
    )
    this.vProgress = VueSelector("ProgressBar")
    this.successToast = Selector(".toasted.success")
  }
}

/******************************************************************************/

export class FeedbackPage {
  constructor() {
    this.fbInput = Selector("textarea.editor-input")
    this.fbReadyBtn = Selector("button").withAttribute(
      "data-test",
      "fb-ready-btn"
    )
    this.fbConfirmBtn = Selector("button").withAttribute(
      "data-test",
      "fb-confirm-btn"
    )
    this.vDiscussion = VueSelector("FeedbackDiscussion")
    this.submission = Selector("#submission_content")
    this.s10fbItem = VueSelector("FeedbackItem").withText("Student 10")
    this.goodLevel = Selector("#Quality0")
    this.submissionTitle = Selector("#submission_content").find("h2")
  }
}

export class HomePage {
  constructor() {
    this.tasks = Selector(".task")
    this.firstTaskBtn = this.tasks
      .nth(0)
      .find("a")
      .withAttribute("data-test", "give-feedback")
    this.tasklist = Selector("#tasklist")
  }
}

export class RubricCreatorPage {
  constructor() {
    this.vRubricCreator = VueSelector("RubricCreator")
    this.rubricNameInput = Selector("#rubric_name")
    this.rubricDescription = Selector("#description")
    this.addCriteriaBtn = Selector("button").withText("Add Criteria")
    this.criteriaZero = Selector("#criteria_0")
    this.cZeroName = this.criteriaZero
      .find("input")
      .withAttribute("data-test", "criteria-name")
    this.cZeroDesc = this.criteriaZero
      .find("textarea")
      .withAttribute("data-test", "criteria-desc")
    this.cZeroAddLvlBtn = this.criteriaZero
      .find("button")
      .withAttribute("data-test", "add-level")
    this.levelZero = this.criteriaZero
      .find("div")
      .withAttribute("data-test", "level_0")
    this.levelOne = this.criteriaZero
      .find("div")
      .withAttribute("data-test", "level_1")
    this.levelTwo = this.criteriaZero
      .find("div")
      .withAttribute("data-test", "level_2")
    this.createRubricBtn = Selector("button").withAttribute(
      "data-test",
      "create-rubric"
    )
  }
}
