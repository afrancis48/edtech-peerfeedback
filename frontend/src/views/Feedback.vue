<template>
  <div class="columns page">
    <content-placeholders
      v-if="submissionLoading || taskLoading"
      class="column col-12"
    >
      <content-placeholders-heading :img="true" />
      <content-placeholders-text />
      <content-placeholders-text />
    </content-placeholders>

    <template v-if="!submissionLoading">
      <div v-if="unauthorized" class="column col-12">
        <empty-state
          title="Unauthorized Access"
          icon="icon-stop"
          message="You are not paired with this submission author."
        >
        </empty-state>
      </div>

      <feedback-writer
        v-if="showWriter"
        :submission="submission"
        :view_only=viewOnly
      ></feedback-writer>
      <feedback-reader
        v-if="showReader"
        :submission="submission"
      ></feedback-reader>
    </template>
  </div>
</template>

<script>
import { mapGetters, mapState } from "vuex"
import FeedbackReader from "../components/feedback/FeedbackReader"
import FeedbackWriter from "../components/feedback/FeedbackWriter"
import EmptyState from "../components/ui/EmptyState"

export default {
  name: "Feedback",
  components: {
    EmptyState,
    FeedbackReader,
    FeedbackWriter
  },
  computed: {
    ...mapGetters("course", ["role"]),
    ...mapGetters("user", ["currentUser"]),
    ...mapState({
      submission: state => state.submission.current,
      submissionLoading: state => state.submission.isLoading,
      task: state => state.task.current,
      noSubmissionTask: state => state.task.noSubmissionTask,
      taskLoading: state => state.task.currentLoading
    }),
    showWriter: function() {
      // the user has a task and it is NOT complete
      //return this.$route.params.view_only
      return this.task !== null && this.task.status !== "COMPLETE"
    },
    viewOnly: function() {
     return this.$route.params.view_only
    },
    showReader: function() {
      // Feedback area will be visible on the following conditions
      return (
        this.role === "ta" ||
        this.role === "teacher" ||
        // submission owner
        parseInt(this.$route.params.user_id) === this.currentUser.id ||
        (!this.noSubmissionTask && this.task.status === "COMPLETE")
      )
    },
    unauthorized: function() {
      return (
        this.noSubmissionTask &&
        this.role !== "ta" &&
        this.role !== "teacher" &&
        parseInt(this.$route.params.user_id) !== this.currentUser.id
      )
    }
  },
  watch: {
    $route: function(to) {
      this.initData(to.params)
    }
  },
  created() {
    this.initData(this.$route.params)
  },
  methods: {
    initData: function(routeParams) {
      const course_id = parseInt(routeParams.course_id)
      this.$store.dispatch("course/setCurrent", course_id)
      this.$store.dispatch("assignment/setCurrent", routeParams)
      this.$store.dispatch("assignment/loadSettings", routeParams)
      this.$store.dispatch("task/getTaskForSubmission", routeParams)
      this.$store.dispatch("submission/getSubmission", routeParams)
    }
  }
}
</script>

<style scoped></style>
