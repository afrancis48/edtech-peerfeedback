<template>
  <section>
    <content-placeholders v-if="isLoading">
      <content-placeholders-heading />
      <content-placeholders-text :lines="3" />
    </content-placeholders>

    <div v-if="!isLoading" class="columns">
      <div class="column col-12">
        <div v-if="assignment.due_at === null" class="text-error p-2 mb-2">
          <small>
            <octicon name="alert" class="icon text-warning"></octicon> The
            assignment doesn't have a deadline. Please set a deadline before
            downloading data.
          </small>
        </div>
      </div>
      <!-- Assignment Data -->
      <div class="column col-12">
        <div class="tile">
          <div class="tile-content">
            <p class="tile-title">Review Data</p>
            <p class="tile-subtitle text-gray">
              Download feedback data for this
              {{
                settings.intra_group_review
                  ? "within-group anonymous review"
                  : "assignment"
              }}
              as a CSV file.
            </p>
          </div>
          <div class="tile-action">
            <button
              class="btn btn-secondary btn-sm"
              :class="{ disabled: assignment.due_at === null }"
              @click="requestData()"
            >
              Get Data
            </button>
          </div>
        </div>
      </div>

      <div class="column col-12">
        <div class="tile">
          <div class="tile-content">
            <p class="tile title">Full Assignment Data</p>
            <p class="tile-subtitle text-gray">
              Download the full details of this assignment.
            </p>
          </div>
          <div class="tile-action">
            <button class="btn btn-secondary btn-sm" @click="getFullData">
              Get Full data
            </button>
          </div>
        </div>
      </div>
      <!-- Student Scores -->
      <div
        v-if="
          settings.use_rubric &&
            settings.rubric_id &&
            !settings.intra_group_review
        "
        class="column col-12 mt-2"
      >
        <div class="tile">
          <div class="tile-content">
            <p class="tile-title">Student Scores</p>
            <p class="tile-subtitle text-gray">
              Download feedback scores of all students. The CSV will contain the
              no.of feedback a student received, the average score and standard
              deviation in the scores
            </p>
          </div>
          <div class="tile-action">
            <button
              class="btn btn-secondary btn-sm"
              :class="{ disabled: assignment.due_at === null }"
              @click="requestScores()"
            >
              Get Data
            </button>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script>
import { mapState } from "vuex"
import assignmentAPI from "../../api/assignment.js"

import Octicon from "vue-octicon/components/Octicon"
import "vue-octicon/icons/alert"

export default {
  name: "AssignmentData",
  components: { Octicon },
  computed: {
    ...mapState({
      isLoading: state => state.assignment.isLoading,
      assignment: state => state.assignment.current,
      settings: state => state.assignment.settings
    })
  },
  methods: {
    showSuccess: function() {
      this.$toasted.info("You will receive a download link via email!", {
        duration: 3000
      })
    },
    showError: function(msg) {
      this.$toasted.error(`There was an error creating your download. ${msg}`, {
        duration: 3000
      })
    },
    requestData: function() {
      const course_id = parseInt(this.$route.params.course_id)
      const assignment_id = parseInt(this.$route.params.assignment_id)
      assignmentAPI
        .exportAssignmentData(course_id, assignment_id)
        .then(this.showSuccess)
        .catch(err => {
          console.log(err)
          this.showError()
        })
    },
    requestScores: function() {
      const course_id = parseInt(this.$route.params.course_id)
      const assignment_id = parseInt(this.$route.params.assignment_id)
      assignmentAPI
        .exportAssignmentScores(course_id, assignment_id)
        .then(this.showSuccess)
        .catch(err => {
          let message = `${err.response.status} ${err.response.statusText}`
          if (err.response.data.hasOwnProperty("message")) {
            message = err.response.data.message
          }
          this.showError(message)
        })
    },
    getFullData: function() {
      const course_id = parseInt(this.$route.params.course_id)
      const assignment_id = parseInt(this.$route.params.assignment_id)
      assignmentAPI
        .exportDetailedData(course_id, assignment_id)
        .then(this.showSuccess)
        .catch(e => {
          console.log(e)
          this.showError()
        })
    }
  }
}
</script>

<style></style>
