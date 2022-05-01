<template>
  <div class="column col-12">
    <button class="btn btn-link" @click="showOptionsModal = true">
      Missing, incorrect or corrupted submission?
    </button>

    <confirm-modal
      title="Missing, incorrect or corrupt submission?"
      :show-modal="showOptionsModal"
      confirm="Replace Task"
      reject="Retry fetching submission"
      @confirmed="showReplaceTaskModal"
      @rejected="retryFetching"
    >
      <p>Submissions may not load properly due to a number of reasons like:</p>
      <ul>
        <li>Your peer hasn't turned in the submission yet</li>
        <li>The uploaded file was corrupt</li>
        <li>There was a network error when loading the file</li>
      </ul>
      <p>
        Kindly retry fetching the submission if no file or text has loaded. In
        case retrying doesn't help, you can replace the current task with a new
        one.
      </p>
    </confirm-modal>

    <transition
      name="fade"
      mode="out-in"
      enter-active-class="animated fadeIn"
      leave-active-class="animated fadeOut"
    >
      <div v-if="job" class="empty">
        <div class="empty-icon"><i class="icon icon-people"></i></div>
        <p class="empty-title h5">Getting you a new peer</p>
        <p class="empty-subtitle">
          Kindly wait while we find you a new peer with a submission to review
        </p>
        <div class="empty-action">
          <progress-bar
            :job-id="job.id"
            @job-completed="onJobCompleted"
          ></progress-bar>
        </div>
      </div>
    </transition>

    <confirm-modal
      title="Replace Task?"
      :show-modal="showReplaceModal"
      confirm="Yes, Replace Task"
      reject="No, Continue writing feedback"
      @confirmed="replaceTask"
      @rejected="showReplaceModal = false"
    >
      <p>
        Replacing the task will delete this task! Any feedback you might have
        already written will be lost. You will be assigned a new task with a
        different submission to review.
      </p>
    </confirm-modal>
  </div>
</template>

<script>
import ProgressBar from "../ui/ProgressBar"
import ConfirmModal from "../ui/ConfirmModal"
import { mapActions } from "vuex"

export default {
  name: "ReplaceTask",
  components: {
    ProgressBar,
    ConfirmModal
  },
  data: function() {
    return {
      job: false,
      error: "",
      showOptionsModal: false,
      showReplaceModal: false
    }
  },
  methods: {
    ...mapActions("task", ["replaceAndGetNewTask"]),
    replaceTask: function() {
      this.showReplaceModal = false
      const self = this
      this.replaceAndGetNewTask()
        .then(job => {
          self.job = job
        })
        .catch(err => {
          self.$toasted.error(err.statusText, { duration: 5000 })
        })
    },
    onJobCompleted: function(result) {
      const self = this
      let { course_id, assignment_id } = { ...this.$route.params }
      if (result.hasOwnProperty("recipient_id")) {
        this.$toasted.success(
          "You are paired with a new peer. Redirecting you to the feedback page ...",
          { duration: 3000 }
        )
        setTimeout(
          () =>
            self.$router.push({
              name: "give-feedback",
              params: { course_id, assignment_id, user_id: result.recipient_id }
            }),
          3000
        )
      } else if (result.hasOwnProperty("message")) {
        this.$toasted.error(result.message, { duration: 5000 })
      } else {
        this.$toasted.error("Something went wrong. Refresh this page.")
      }
    },
    showReplaceTaskModal: function() {
      this.showOptionsModal = false
      this.showReplaceModal = true
    },
    retryFetching: function() {
      this.showOptionsModal = false
      this.$store.dispatch("submission/refetchSubmission", this.$route.params)
    }
  }
}
</script>

<style scoped></style>
