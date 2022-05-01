<template>
  <section>
    <h2>Assignment Settings</h2>

    <content-placeholders v-if="isLoading">
      <content-placeholders-heading />
      <content-placeholders-text :lines="3" />
    </content-placeholders>

    <form v-if="!isLoading" class="form-horizontal">
      <div v-if="!settings.intra_group_review" class="form-group">
        <label class="form-switch">
          <input v-model="settings.allow_student_pairing" type="checkbox" />
          <i class="form-icon"></i> Students can pair themselves
        </label>
      </div>

      <div
        v-if="!settings.intra_group_review"
        class="form-group columns"
        :class="{ 'has-error': !reviewCountValid }"
      >
        <div class="column col-7">
          <label class="form-label" for="maxReviews">
            Maximum extra review tasks per student
          </label>
        </div>
        <div class="column col-5">
          <input
            id="maxReviews"
            v-model="settings.max_reviews"
            type="number"
            min="0"
            class="form-input"
            :disabled="!settings.allow_student_pairing"
          />
          <p v-if="!reviewCountValid" class="form-input-hint">
            There cannot be more reviews per submission than the no.of students
            enrolled in the course
          </p>
        </div>
      </div>
      <div class="form-horizontal">
        <label class="form-switch">
          <input v-model="settings.allow_view_peer_assignments" type="checkbox" />
          <i class="form-icon"></i> Students can view peer assignments
        </label>
      </div>
      <div class="form-group columns">
        <div class="column col-7">
          <label class="form-switch">
            <input
              v-model="settings.use_rubric"
              type="checkbox"
              data-test="use-rubric"
              @change="rubricUsageToggled()"
            />
            <i class="form-icon"></i> Use rubric for assessment
          </label>
        </div>
        <div
          v-if="checkingAffected"
          class="column col-5 bg-secondary text-primary pt-1"
        >
          <small>
            <octicon name="info" class="icon" /> Checking if this change affects
            any feedback
          </small>
        </div>
      </div>


      <div class="form-group columns">
        <div class="column col-7 col-sm-12">
          <label for="rubric" class="form-label">Assessment Rubric</label>
        </div>
        <div class="column col-5 col-sm-12">
          <select
            id="rubric"
            v-model="settings.rubric_id"
            name="rubric"
            class="form-select"
            :disabled="!settings.use_rubric"
            @change="rubricChanged"
          >
            <option value="0" disabled selected>Select Rubric</option>
            <option v-for="ruby in rubrics" :key="ruby.id" :value="ruby.id">
              {{ ruby.name }}
            </option>
            <option disabled>──────────</option>
            <option value="creator">Create a new Rubric</option>
          </select>
        </div>
      </div>

      <div class="form-group columns">
        <div class="column col-5 col-sm-12">
          <label for="feedback_deadline" class="form-label">
            Feedback Deadline
          </label>
        </div>
        <div class="column col-7 col-sm-12">
          <div class="input-group">
            <input
              v-if="settings.deadline_format === 'canvas'"
              id="feedback_deadline"
              v-model="settings.feedback_deadline"
              type="number"
              min="0"
              class="form-input"
              :disabled="assignment.due_at === null"
            />
            <datetime
              v-else
              v-model="settings.custom_deadline"
              type="datetime"
              class="input-group"
              input-class="form-input"
              format="MMM d, y t"
              :use12-hour="true"
            />
            <select v-model="settings.deadline_format" class="form-select">
              <option value="canvas"> days after Canvas due </option>
              <option value="custom"> Custom Date </option>
            </select>
          </div>
        </div>

        <div
          v-if="assignment.due_at || settings.deadline_format === 'custom'"
          class="column col-7 col-ml-auto col-sm-12"
        >
          <p class="mt-2 text-info">
            <small>
              <time>{{ feedbackDueDate | readableDate }}</time>
            </small>
          </p>
        </div>

        <div
          v-if="!assignment.due_at && settings.deadline_format === 'canvas'"
          class="text-error column col-12"
        >
          <small>
            <octicon name="alert" class="icon text-warning" /> Set assignment
            deadline in Canvas to be able to set feedback deadline relative to
            Canvas
          </small>
        </div>

        <div
          v-if="assignment.due_at || settings.deadline_format === 'custom'"
          class="column col-12"
        >
          <p class="text-info">
            <octicon name="info" class="icon" /> A reminder email will be sent
            to students 5 days before the feedback deadline to complete their
            unfinished review tasks.
          </p>
        </div>
      </div>

      <div v-if="!isLoading">
        <div class="form-group">
          <label class="form-switch">
            <input v-model="settings.intra_group_review" type="checkbox" />
            <i class="form-icon"></i> Within-group anonymous review
            <span
              class="tooltip tooltip-right c-hand ml-2"
              data-tooltip="Each student will provide anonymous feedback to all other students in the same group. In other words, every student in a group will receive feedback from all other members in the group, but will not know which feedback comes from which member."
            >
              <octicon class="icon text-info" name="info" />
            </span>
          </label>
        </div>
      </div>

      <p>
        <span class="bg-secondary text-primary p-1 rounded">
          Feedback prompt for this assignment:
        </span>
      </p>
      <markdown-editor
        v-model="settings.feedback_suggestion"
        :initial-text="getFeedbackSuggestion"
      />

      <div v-if="!settings.intra_group_review" class="form-group">
        <label class="form-switch">
          <input v-model="settings.filter_pdf" type="checkbox" />
          <i class="form-icon"></i> Show only PDF files for peer review
        </label>
      </div>
    </form>


    <button
      class="btn btn-primary float-right"
      data-test="save-button"
      :class="{ loading: savingSettings }"
      :disabled="!reviewCountValid"
      @click="saveSettings"
    >
      Save
    </button>

    <div
      id="rubricCheckModal"
      class="modal"
      :class="{ active: affectedFeedback }"
    >
      <div class="modal-overlay"></div>
      <div class="modal-container">
        <div class="modal-header">
          <div class="modal-title h5">Changing Rubrics</div>
        </div>
        <div v-if="oldRubric" class="modal-body">
          <div v-if="settings.use_rubric" class="content">
            <p>
              {{ affectedFeedback }} reviews have already been submitted using
              the previous Rubric.
            </p>
            <div class="form-group">
              <label class="form-label">How should they be affected?</label>
              <label class="form-radio">
                <input
                  v-model="rubricChangeAction"
                  type="radio"
                  name="rubricChangeAction"
                  value="reopen"
                />
                <i class="form-icon"></i> Re-open all reviews with the old
                rubric and notify students to resubmit using the new rubric
              </label>
              <label class="form-radio">
                <input
                  v-model="rubricChangeAction"
                  type="radio"
                  name="rubricChangeAction"
                  value="disable"
                />
                <i class="form-icon"></i> Disable the scores based on old rubric
                and don't show scores in the reviews
              </label>
            </div>
          </div>
          <div v-else class="content">
            <p>
              {{ affectedFeedback }} reviews have already been submitted using
              the previous rubric.
            </p>
            <div class="form-group">
              <div class="form-label">How should they be affected?</div>
              <label class="form-radio">
                <input
                  v-model="rubricChangeAction"
                  type="radio"
                  name="rubricChangeAction"
                  value="update_new"
                />
                <i class="form-icon"></i> Keep the scores on the feedback and
                show it to recipients.
              </label>
              <label class="form-radio">
                <input
                  v-model="rubricChangeAction"
                  type="radio"
                  name="rubricChangeAction"
                  value="disable"
                />
                <i class="form-icon"></i> Disable the scores based on old rubric
                and don't show scores in the reviews
              </label>
            </div>
          </div>
        </div>
        <div v-else class="modal-body">
          <div class="content">
            <p>
              {{ affectedFeedback }} reviews have already been submitted without
              any rubric based evaluation and scores.
            </p>
            <div class="form-group">
              <label class="form-label">How should they be affected?</label>
              <label class="form-radio">
                <input
                  v-model="rubricChangeAction"
                  type="radio"
                  name="rubricChangeAction"
                  value="reopen"
                />
                <i class="form-icon"></i> Re-open the reviews and notify the
                students to evaluate using the rubric
              </label>
              <label class="form-radio">
                <input
                  v-model="rubricChangeAction"
                  type="radio"
                  name="rubricChangeAction"
                  value="update_new"
                />
                <octicon name="info" class="icon" /> Don't affect the reviews
                submitted in anyway. Use rubric in all future reviews
              </label>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-default" @click="revertRubric()">
            Don't Change Rubric
          </button>
          <button
            class="btn btn-primary ml-2"
            :disabled="!rubricChangeAction"
            @click="closeModalAndSave()"
          >
            Change Rubric
          </button>
        </div>
      </div>
    </div>
  </section>
</template>
<script>
import { mapState, mapActions } from "vuex"
import Octicon from "vue-octicon/components/Octicon"
import "vue-octicon/icons/settings"
import "vue-octicon/icons/alert"
import "vue-octicon/icons/question"
import "vue-octicon/icons/info"
import MarkdownEditor from "../ui/MarkdownEditor"
import { Datetime } from "vue-datetime"
import "vue-datetime/dist/vue-datetime.css"

export default {
  name: "AssignmentSettings",
  components: {
    Octicon,
    Datetime,
    MarkdownEditor
  },
  data: function() {
    return {
      savingSettings: false,
      rubricChangeAction: false,
      affectedFeedback: 0,
      oldRubric: 0,
      checkingAffected: false
    }
  },
  computed: {
    ...mapState({
      isLoading: state => state.assignment.settingsLoading,
      rubrics: state => state.rubric.all,
      assignment: state => state.assignment.current
    }),
    settings: {
      get() {
        return this.$store.state.assignment.settings
      },
      set(value) {
        this.$store.commit("assignment/setSettings", value)
      }
    },
    feedbackDueDate: function() {
      if (this.settings.deadline_format === "custom") {
        return this.settings.custom_deadline
      }
      let assignmentDueDate = new Date(this.assignment.due_at)

      return assignmentDueDate.setDate(
        assignmentDueDate.getDate() + parseInt(this.settings.feedback_deadline)
      )
    },
    getFeedbackSuggestion: function() {
        return this.settings.feedback_suggestion
    }
  },
  created() {
    this.$store.dispatch("rubric/getAllRubrics")
  },
  methods: {
    ...mapActions("assignment", [
      "updateSettings",
      "getAffectedByRubricChange"
    ]),
    rubricChanged: function() {
      if (this.settings.rubric_id === "creator") {
        this.$router.push({ name: "rubric-creator" })
        return
      }
      const self = this
      self.checkingAffected = true

      self
        .getAffectedByRubricChange()
        .then(affected => {
          self.affectedFeedback = affected.feedback_count
          if (affected.rubric_id === null) {
            self.oldRubric = 0
          } else {
            self.oldRubric = affected.rubric_id
          }
          self.checkingAffected = false
        })
        .catch(err => {
          console.log(err)
          self.checkingAffected = false
        })
    },
    rubricUsageToggled: function() {
      // check for affected feedback when rubric is disabled
      if (!this.settings.use_rubric && this.settings.rubric_id) {
        this.rubricChanged()
      }
    },
    revertRubric: function() {
      this.settings.rubric_id = this.oldRubric
      this.affectedFeedback = 0
    },
    closeModalAndSave: function() {
      this.affectedFeedback = 0
      this.saveSettings()
    },
    saveSettings: function() {
      const self = this
      self.savingSettings = true

      if (this.settings.use_rubric && !this.settings.rubric_id) {
        alert(
          "You have chosen to use a rubric for evaluation, but haven't selected a rubric."
        )
        self.savingSettings = false
        return
      }

      self
        .updateSettings(self.rubricChangeAction)
        .then(() => {
          self.$toasted.success("Settings saved.", { duration: 2000 })
          self.savingSettings = false
        })
        .catch(error => {
          self.$toasted.error(
            `Failed to save Settings. ${error.response.status} ${
              error.response.statusText
            }`,
            { duration: 5000 }
          )
          self.savingSettings = false
        })
    },
    reviewCountValid: function() {
      return (
        parseInt(this.settings.max_reviews) < this.assignment.students.length
      )
    }
  }
}
</script>
<style scoped>
.text-info {
  color: #7f9cf5;
}

.tooltip.tooltip-right::after {
  display: block;
  position: relative;
  left: 80%;
  white-space: pre-wrap;
}
</style>
