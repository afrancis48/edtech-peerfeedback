<template>
  <div>
    <div class="bar">
      <div class="bar-item" :style="{ width: progressValue + '%' }">
        {{ progressValue }}%
      </div>
    </div>
    <div v-if="error" class="text-error">
      <small>{{ error }}</small>
    </div>
  </div>
</template>

<script>
import jobAPI from "../../api/job"

export default {
  name: "ProgressBar",
  props: {
    jobId: {
      type: String,
      required: true
    },
    pollingInterval: {
      type: Number,
      required: false,
      default: 2000
    }
  },
  data: function() {
    return {
      pollingId: null,
      error: false,
      progressValue: 5
    }
  },
  created() {
    this.pollingId = setInterval(this.updateJobStatus, this.pollingInterval)
  },
  methods: {
    updateJobStatus: function() {
      const vm = this
      jobAPI
        .getJobStatus(vm.jobId)
        .then(job => {
          if (job.status === "in_progress") {
            vm.progressValue = job.progress
            return
          }

          if (job.status === "error") {
            vm.error = job.message
            if (job.message) {
              vm.$toasted.error(job.message)
            }
          } else if (job.status === "success") {
            vm.progressValue = 100
            if (job.message) {
              vm.$toasted.success(job.message, { duration: 3000 })
            }
          }
          vm.$emit("job-completed", job)
          clearInterval(vm.pollingId)
        })
        .catch(error => {
          console.log("Cannot get status of Job with ID: ", vm.jobId, error)
        })
    }
  }
}
</script>

<style scoped></style>
