<template>
  <section class="page">
    <div class="columns">
      <div class="column col-12"><h2>Data Exports</h2></div>
      <div class="column col-6">
        <div class="form-group">
          <label class="form-radio">
            <input
              v-model="export_type"
              type="radio"
              name="export_type"
              value="course"
            />
            <i class="form-icon"></i> Entire Course
          </label>
          <label class="form-radio">
            <input
              v-model="export_type"
              type="radio"
              name="export_type"
              value="assignment"
            />
            <i class="form-icon"></i> All the data of an assignment
          </label>
          <label class="form-radio">
            <input
              v-model="export_type"
              type="radio"
              name="export_type"
              value="peer_grades"
            />
            <i class="form-icon"></i> Peer Grades of an assignment
          </label>
        </div>
        <div class="form-group">
          <label class="form-checkbox">
            <input v-model="ai_feedback" type="checkbox" />
            <i class="form-icon"></i> Update AI Feedback Evaluations
          </label>
          <label class="form-checkbox">
            <input v-model="include_drafts" type="checkbox" />
            <i class="form-icon"></i> Include feedback that has not been
            submitted (drafts)
          </label>
        </div>
        <button
          class="btn btn-primary my-2"
          :disabled="requestBtnDisabled"
          @click="request_data"
        >
          Request Data
        </button>
      </div>
      <div class="column col-6">
        <div class="form-group" :class="{ 'has-error': requestBtnDisabled }">
          <label
            for="assignment"
            class="form-label"
            :class="{ 'text-gray': export_type === 'course' }"
          >
            Assignment
          </label>
          <select
            id="assignment"
            v-model.number="assignment_id"
            name="assignment"
            class="form-select"
            :disabled="export_type === 'course'"
          >
            <option value="0">Select an Assignment</option>
            <option
              v-for="assignment in assignments"
              :key="assignment.id"
              :value="assignment.id"
            >
              {{ assignment.name }}
            </option>
          </select>
          <p v-if="requestBtnDisabled" class="form-input-hint">
            An Assignment should be chosen for this export
          </p>
        </div>
      </div>
    </div>
  </section>
</template>

<script>
import { mapState } from "vuex"
import courseAPI from "../api/course"
import assignmentAPI from "../api/assignment"

export default {
  name: "DataExporter",
  data: function() {
    return {
      ai_feedback: false,
      include_drafts: false,
      export_type: "course",
      assignment_id: 0
    }
  },
  computed: {
    ...mapState({
      assignments: state => state.assignment.all
    }),
    requestBtnDisabled: function() {
      return (
        (this.export_type === "assignment" ||
          this.export_type === "peer_grades") &&
        !this.assignment_id
      )
    }
  },
  created() {
    const course_id = +this.$route.params.id
    this.$store.dispatch("assignment/getAssignmentsInCourse", course_id)
    this.$store.dispatch("course/setCurrent", course_id)
  },
  methods: {
    request_data: function() {
      const course_id = +this.$route.params.id
      const data = {
        include_drafts: this.include_drafts,
        ai_feedback: this.ai_feedback,
        course_id: course_id,
        assignment_id: this.assignment_id
      }
      if (this.export_type === "course") {
        courseAPI.getData(data, this.showSuccess, this.showError)
      } else if (this.export_type === "assignment") {
        assignmentAPI
          .exportAssignmentData(course_id, this.assignment_id)
          .then(this.showSuccess)
          .catch(this.showError)
      } else if (this.export_type === "peer_grades") {
        assignmentAPI
          .exportAssignmentScores(course_id, this.assignment_id)
          .then(this.showSuccess)
          .catch(this.showError)
      }
    },
    showSuccess: function() {
      this.$toasted.success(
        "Your request has been placed. You will receive an email with the details.",
        { duration: 3000 }
      )
    },
    showError: function(error) {
      let message = "The data request has failed. "
      message += error.response.data.hasOwnProperty("message")
        ? error.response.data.message
        : error.response.status
      this.$toasted.error(message, {
        duration: 3000
      })
    }
  }
}
</script>

<style scoped></style>
