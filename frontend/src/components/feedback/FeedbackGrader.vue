<template>
  <div>
    <content-placeholders v-if="loadingFeedback">
      <content-placeholders-heading />
      <content-placeholders-text />
    </content-placeholders>
    <div v-if="!viewOnly && !loadingFeedback" class="column col-12 pt-2">
      <div v-show="currentStep === 'grading'" id="feedback_input_area">
        <h2>
          Your Feedback
          {{
            settings.intra_group_review ? ` for ${feedback.receiver.name}` : ""
          }}
        </h2>
        <p class="text-gray">
          Give your earnest thoughts on your classmates' work and try to help
          them improve in any way you can.
        </p>
        <p v-if="settings.intra_group_review">
          <span class="bg-secondary text-primary p-1 rounded">
            Writing a feedback is optional
          </span>
        </p>
        <markdown-editor
          v-model="feedbackText"
          :initial-text="feedback.value"
          :feedback-suggestion="settings.feedback_suggestion"
          @save-draft="saveFeedback()"
        />
        <p v-show="feedbackIncomplete">
          <span class="label label-light m-2">Please write a bit more</span>
        </p>

        <div v-if="rubricAvailable" class="mt-2 pt-2">
          <rubric-grader
            v-model="grades"
            :initial-grades="feedback.grades || []"
            :rubric-id="feedback.rubric_id"
          />
        </div>

        <div id="ai-scoreboard">
          <feedback-grader-a-i-score :value="feedbackText">
          </feedback-grader-a-i-score>
        </div>

        <div class="form-group my-2">
          <button
            class="btn btn-default"
            :class="{ loading: savingFeedback && isDraft }"
            @click="saveFeedback()"
          >
            Save Draft
          </button>
          <button
            class="btn btn-primary ml-2"
            :class="{ loading: savingFeedback && !isDraft }"
            data-test="fb-ready-btn"
            :disabled="savingFeedback || feedbackIncomplete || rubricIncomplete"
            @click="currentStep = 'revisingFeedback'"
          >
            Ready to Revise <i class="icon icon-arrow-right" />
          </button>
        </div>
      </div>

      <feedback-confirm-panel
        v-if="currentStep === 'revisingFeedback'"
        :feedback="feedbackText"
        :is-final="!rubricAvailable && !showSubmissionWarning"
        @change-step="setCurrentStep"
      />

      <rubric-confirm-panel
        v-if="currentStep === 'revisingRubric' && rubricAvailable"
        :grades="grades"
        :rubric="rubricWithId(feedback.rubric)"
        :is-final="!showSubmissionWarning"
        @change-step="setCurrentStep"
      />

      <final-confirm-panel
        v-if="currentStep === 'finalConfirm'"
        @change-step="setCurrentStep"
        @save-feedback="onFinalConfirm"
      />

      <feedback-steps
        :rubric-available="rubricAvailable"
        :current-step="currentStep"
        @change-step="setCurrentStep"
      />
    </div>
    <!-- Congratulation message modal -->
    <modal
      v-if="showCongratsModal"
      :show-modal="showCongratsModal"
      title="Congratulations!"
      class="text-center congrats-modal"
      @modalClosed="closeCongratsModal()"
    >
      <p ref="burst">
        Thank you for quickly giving feedback to all of your peers. Early
        feedback helps your classmates the most.
      </p>
      <img
        src="../../assets/monster.png"
        alt=":)"
        class="animated bounce"
        width="200"
      />
      <div
        v-if="
          settings.allow_student_pairing && extrasGiven < settings.max_reviews
        "
      >
        <p>
          You can give feedback to more peers by requesting extra feedback
          tasks.
        </p>
        <button class="btn btn-primary" @click="$router.push(assignmentPage)">
          Get an extra feedback task
        </button>
      </div>
      <div class="my-2">
        <p>Are you enjoying Peer Feedback? Have ideas? Share your thoughts.</p>
        <p>
          <mark>
            <a
              href="mailto:gabriel@peerfeedback.io?Subject=Peer Feedback"
              class="mt-2"
            >
              Mail
            </a>

            or

            <a
              href="https://twitter.com/intent/tweet?text=@peerfeedbackai%20"
              class="mt-2"
            >
              Tweet
            </a>

            to us!
          </mark>
        </p>
      </div>
    </modal>
  </div>
</template>

<script>
import { mapState, mapGetters } from "vuex"
import RubricGrader from "../rubric/RubricGrader"
import MarkdownEditor from "../ui/MarkdownEditor"
import FeedbackGraderAIScore from "./FeedbackGraderAIScore"
import { TimeTracker } from "./timetracker"
import { confetti } from "dom-confetti"
import Modal from "../ui/Modal"
import FeedbackSteps from "./FeedbackSteps"
import FeedbackConfirmPanel from "./FeedbackConfirmPanel"
import RubricConfirmPanel from "./RubricConfirmPanel"
import FinalConfirmPanel from "./FinalConfirmPanel"

export default {
  name: "FeedbackGrader",
  components: {
    RubricGrader,
    MarkdownEditor,
    FeedbackGraderAIScore,
    FeedbackSteps,
    FeedbackConfirmPanel,
    RubricConfirmPanel,
    FinalConfirmPanel,
    Modal
  },
  mixins: [TimeTracker],
  props: {
    saveContent: {
      type: Number,
      default: 0
    },
      view_only: {
        type: String,
        required: false,
        default: "false"
      }
  },
  data: function() {
    return {
      feedbackText: "",
      grades: [],
      isDraft: true,
      currentStep: "grading",
      emitElapsedTime: false,
      showCongratsModal: false
    }
  },
  computed: {
    ...mapState({
      feedback: state => state.feedback.current,
      loadingFeedback: state => state.feedback.currentLoading,
      savingFeedback: state => state.feedback.currentUpdating,
      tasks: state => state.tasks.tasks,
      extrasGiven: state => state.feedback.extrasGiven,
      previousWriteTime: state => state.feedback.previousWriteTime,
      assignment: state => state.assignment.current
    }),
    ...mapState("assignment", ["settings"]),
    ...mapGetters("task", ["incompleteTasks"]),
    ...mapGetters("rubric", ["rubricWithId"]),
    ...mapGetters("user", ["showSubmissionWarning"]),
    feedbackIncomplete: function() {
      // Ensure there are 10 words in the feedback when submitting feedback
      return (
        !this.settings.intra_group_review && // text feedback is optional for IGR
        this.feedbackText &&
        this.feedbackText.trim().split(/\s+/).length < 10
      )
    },
    rubricIncomplete: function() {
      const rubric = this.rubricWithId(this.feedback.rubric_id)
      if (!rubric) return

      if (rubric.hasOwnProperty("criterions")) {
        let complete = this.grades.reduce(
          (acc, cur) => acc & Number.isInteger(cur.level),
          true
        )
        if (!complete || rubric.criterions.length !== this.grades.length) {
          return true
        }
      }
      return false
    },
    assignmentPage: function() {
      const course_id = parseInt(this.$route.params.course_id)
      const assignment_id = parseInt(this.$route.params.assignment_id)
      return {
        name: "assignment",
        params: { course_id, assignment_id }
      }
    },
    feedbackDueDate: function() {
      if (!this.assignment.due_at) {
        let now = new Date()
        let tomorrow = new Date()
        tomorrow.setDate(now.getDate() + 1)
        return tomorrow
      }

      let assignmentDueDate = new Date(this.assignment.due_at)
      let updatedDueDate = new Date(assignmentDueDate)

      return updatedDueDate.setDate(
        updatedDueDate.getDate() + parseInt(this.settings.feedback_deadline)
      )
    },
    viewOnly: function() {
      if (this.view_only === "true")
        return true
      else
        return false
    },
    rubricAvailable: function() {
      return !!this.feedback.rubric_id
    }
  },
  watch: {
    saveContent: function() {
      this.saveFeedback()
    }
  },
  created() {
    const routeParams = this.$route.params

    this.$store.dispatch("feedback/getMyFeedbackForSubmission", routeParams)

    const course_id = parseInt(routeParams.course_id)
    const assignment_id = parseInt(routeParams.assignment_id)
    const params = { course_id, assignment_id }

    this.$store.dispatch("task/getCourseTasks", course_id)
    this.$store.dispatch("feedback/getExtraFeedbackGiven", params)
    this.$store.dispatch("user/getSettings")
  },
  methods: {
    setCurrentStep: function(direction) {
      const step1 = "grading"
      const step2 = "revisingFeedback"
      const step3 = "revisingRubric"
      const step4 = "finalConfirm"

      const back = "back"

      if (this.currentStep === step2) {
        if (direction === back) {
          this.currentStep = step1
        } else {
          if (this.rubricAvailable) {
            this.currentStep = step3
          } else {
            if (this.showSubmissionWarning) {
              this.currentStep = step4
            } else {
              this.saveFeedback(false)
            }
          }
        }
      } else if (this.currentStep === step3) {
        if (direction === back) {
          this.currentStep = step2
        } else {
          if (this.showSubmissionWarning) {
            this.currentStep = step4
          } else {
            this.saveFeedback(false)
          }
        }
      } else {
        if (this.rubricAvailable) {
          this.currentStep = step3
        } else {
          this.currentStep = step2
        }
      }
    },
    offerNextTask: function(nextTask) {
      const self = this
      this.updateTasks()
      this.$toasted.info("Feedback saved!!", {
        duration: 8500,
        action: {
          text: "Give feedback to next peer",
          onClick: (e, toastObject) => {
            self.$router.push({
              name: "give-feedback",
              params: {
                course_id: nextTask.course_id,
                assignment_id: nextTask.assignment_id,
                user_id: nextTask.pairing.recipient.id
              }
            })
            toastObject.goAway(0)
          }
        }
      })
    },
    offerExtraTask: function() {
      const self = this
      this.$toasted.info("Feedback Saved!!", {
        duration: 8500,
        action: {
          text: "Get an extra feedback task",
          onClick: (e, toastObj) => {
            self.$router.push(self.assignmentPage)
            toastObj.goAway(0)
          }
        }
      })
    },
    saveFeedback: function(draft = true) {
      this.isDraft = draft
      // prevent multiple put requests from firing
      if (this.savingFeedback) return

      const self = this
      let feedbackData = {
        value: this.feedbackText ? this.feedbackText.trim() : "",
        grades: this.grades,
        draft: draft,
        write_time: this.previousWriteTime + this.getElapsedTime()
      }

      this.$store
        .dispatch("feedback/updateCurrentFeedback", feedbackData)
        .then(fb => {
          self.$emit("saved")
          if (fb.draft) return

          // Check for the next task in the current assignment
          let currentRecipientId = parseInt(self.$route.params.user_id)
          let incompleteTasks = self.incompleteTasks.filter(
            task =>
              task.pairing.recipient.id !== currentRecipientId &&
              task.assignment_id === fb.assignment_id
          )

          if (incompleteTasks.length) {
            let nextTask = incompleteTasks.pop()
            self.offerNextTask(nextTask)
          } else if (new Date() < self.feedbackDueDate) {
            // All tasks were completed before the deadline
            self.showCongratsModal = true
            setTimeout(() => {
              confetti(self.$refs.burst, {
                spread: 120,
                elementCount: 250,
                angle: 0,
                duration: 5000
              })
            }, 1000)
          } else {
            // tasks completed after the deadline is over, just show the toasts
            self.updateTasks()
            if (
              self.settings.allow_student_pairing &&
              self.extrasGiven < self.settings.max_reviews
            ) {
              self.offerExtraTask()
            } else {
              self.$toasted.success(
                "Completed all tasks for this assignment!",
                { duration: 5000 }
              )
            }
          }
        })
        .catch(err => {
          let message = "Failed to save feedback! "
          if (typeof err.response !== "undefined") {
            if (err.response.data.hasOwnProperty("message")) {
              message += err.response.data.message
            } else {
              message += `${err.response.status} ${err.response.statusText}`
            }
          } else {
            message += err.message
          }
          self.$toasted.error(message, { duration: 5000 })
        })
    },
    updateTasks() {
      // update the task to reflect the completed status
      let params = {
        course_id: parseInt(this.$route.params.course_id),
        assignment_id: parseInt(this.$route.params.assignment_id),
        user_id: parseInt(this.$route.params.user_id),
        force: true
      }
      this.$store.dispatch("task/getTaskForSubmission", params)
    },
    closeCongratsModal() {
      this.updateTasks()
      this.showCongratsModal = false
    },
    onFinalConfirm(disable_final_warning) {
      if (disable_final_warning) {
        this.$store.dispatch("user/disableSubmissionWarning")
      }
      this.saveFeedback(false)
    }
  }
}
</script>

<style lang="scss">
.congrats-modal .modal-container .modal-body {
  overflow: hidden;
}
</style>
