<template>
  <section>
    <div class="columns">
      <div
        v-if="
          !settings.intra_group_review &&
            assignment.group_category_id &&
            !assignment.intra_group_peer_reviews
        "
        class="column col-12"
      >
        <p class="bg-gray p-2">
          <small>
            <octicon name="info" class="icon"></octicon> This is a group
            assignment with within-group anonymous reviews disabled. Auto
            pairing will ensure students from the
            <strong>same group are not reviewing each other</strong>. If you
            wish to change this, kindly change the
            <a :href="canvasLink">settings in Canvas.</a>
          </small>
        </p>
      </div>
      <div v-if="!settings.intra_group_review" class="column col-9 col-xs-12">
        <label class="form-label">
          How many assignments should each student grade?
        </label>
      </div>
      <div v-if="!settings.intra_group_review" class="column col-3 col-xs-12">
        <input
          v-model.number="reviewRounds"
          class="form-input"
          type="number"
          data-test="pairs-input"
          min="0"
        />
      </div>
      <div v-if="!settings.intra_group_review" class="column col-12">
        <label class="form-switch">
          <input v-model="excludeDefaulters" type="checkbox" />
          <i class="form-icon"></i> Students who didn't submit should not get
          feedback tasks
        </label>
      </div>
      <div class="column col-12">
        <label class="form-switch">
          <input v-model="showExcludeInput" type="checkbox" />
          <i class="form-icon"></i> Exclude students with GT username
        </label>
        <textarea
          v-show="showExcludeInput"
          id="students"
          v-model="excludedStudents"
          name="students"
          cols="30"
          rows="2"
          class="form-input"
          placeholder="Student 1 GT username, Student 2 GT username, ..."
        ></textarea>
      </div>
      <div v-if="scheduledJob" class="column col-12">
        <p class="bg-gray p-2">
          <small>
            <octicon name="info" class="icon"></octicon> Automatic pairing of
            <strong>{{ scheduledJob.pairs }} peers</strong> per student has been
            scheduled to run on <em>{{ scheduledJob.date | readableDate }}</em>
          </small>
        </p>
      </div>
      <div class="column col-12 mt-2">
        <transition
          name="fade"
          mode="out-in"
          enter-active-class="animated fadeIn"
          leave-active-class="animated fadeOut"
        >
          <div v-if="job">
            <progress-bar
              :job-id="job.id"
              @job-completed="clearJob()"
            ></progress-bar>
          </div>
        </transition>
        <button
          v-if="scheduledJob"
          class="btn btn-error"
          @click="confirmAndCancelScheduledJob"
        >
          Cancel Scheduled Pairing
        </button>
        <button
          v-else
          class="btn my-2"
          :disabled="disableBtns"
          @click="showScheduleSelector = true"
        >
          Schedule Auto Pairing
        </button>
        <button
          class="btn btn-primary my-2 ml-2 float-right"
          data-test="auto-pair-btn"
          :disabled="disableBtns"
          @click="confirmInputs(false)"
        >
          Pair Students
        </button>
      </div>
    </div>

    <div
      id="schedule-selector"
      class="modal"
      :class="{ active: showScheduleSelector }"
    >
      <div class="modal-overlay"></div>
      <div class="modal-container">
        <div class="modal-header">
          <div class="modal-title h5">
            When do you want to schedule the pairing?
          </div>
        </div>
        <div class="modal-body">
          <div class="content">
            <div class="form-group">
              <label class="form-radio">
                <input
                  v-model="scheduleType"
                  type="radio"
                  name="schedule-type"
                  value="canvas"
                />
                <i class="form-icon"></i> 1 hour after the Canvas Assignment due
                <small>({{ hourAfterDue | readableDate }})</small>
              </label>
              <label class="form-radio">
                <input
                  v-model="scheduleType"
                  type="radio"
                  name="schedule-type"
                  value="custom"
                />
                <i class="form-icon"></i> Custom Date and Time
              </label>
            </div>
          </div>
          <div v-if="scheduleType === 'custom'" class="form-group m-2">
            <datetime
              v-model="scheduleTime"
              type="datetime"
              class="input-group"
              input-class="form-input"
              format="MMM d, y hh:mm a"
              :use12-hour="true"
            >
            </datetime>
            <small v-show="scheduleTimeError" class="text-error">
              {{ scheduleTimeError }}
            </small>
          </div>
          <!-- content -->
        </div>
        <div class="modal-footer">
          <button
            class="btn btn-secondary"
            @click="showScheduleSelector = false"
          >
            Cancel
          </button>
          <button class="btn btn-primary ml-2" @click="checkScheduleAndPair">
            Schedule Pairing
          </button>
        </div>
      </div>
    </div>

    <div
      id="autopair-confirm-modal"
      class="modal"
      :class="{ active: showConfirmModal }"
    >
      <div class="modal-overlay"></div>
      <div class="modal-container">
        <div class="modal-header">
          <div class="modal-title h5">
            Do you want to pair students with the following settings?
          </div>
        </div>
        <div class="modal-body">
          <div class="content">
            <table class="table table-narrow table-striped">
              <tbody>
                <tr v-if="settings.intra_group_review">
                  <td>Number of tasks done by a student</td>
                  <td>Every member of group</td>
                </tr>
                <tr v-else>
                  <td>Number of tasks per student</td>
                  <td>{{ reviewRounds }}</td>
                </tr>
                <tr v-if="!settings.intra_group_review">
                  <td>
                    Assign tasks only to students who have submitted the
                    assignment
                  </td>
                  <td>
                    <i
                      v-if="excludeDefaulters"
                      class="icon icon-check text-success"
                    ></i>
                    <i v-else class="icon icon-cross text-error"></i>
                  </td>
                </tr>
                <tr>
                  <td>Use a rubric for evaluating the submissions</td>
                  <td>
                    <i
                      v-if="useRubric"
                      class="icon icon-check text-success"
                    ></i>
                    <i v-else class="icon icon-cross text-error"></i>
                  </td>
                </tr>
                <tr v-if="useRubric">
                  <td>Rubric to use for evaluation</td>
                  <td>{{ rubricName }}</td>
                </tr>
              </tbody>
            </table>

            <div class="toast">
              <octicon name="info" class="icon"></octicon> Emails will be sent
              to the graders informing them about the assignments to be graded.
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-default" @click="showConfirmModal = false">
            <i class="icon icon-arrow-left"></i> No, I need to change a few
            things
          </button>
          <button
            class="btn btn-primary ml-2"
            data-test="pair-confirm-btn"
            @click="pairStudents"
          >
            <i class="icon icon-check"></i> Yes, pair students
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<script>
import { mapActions, mapGetters, mapState } from "vuex"
import ProgressBar from "../ui/ProgressBar"
import { PairingMixin } from "./mixins"
import Octicon from "vue-octicon/components/Octicon"
import "vue-octicon/icons/info"
import { Datetime } from "vue-datetime"
import "vue-datetime/dist/vue-datetime.css"
import { CANVAS_BASE_URL } from "@/config"

export default {
  name: "AutomaticPairingTab",
  components: {
    ProgressBar,
    Octicon,
    Datetime
  },
  mixins: [PairingMixin],
  data: () => {
    return {
      isLoading: false,
      pairingError: "",
      reviewRounds: 0,
      excludeDefaulters: false,
      showConfirmModal: false,
      schedule: false,
      showScheduleSelector: false,
      scheduleType: "canvas",
      scheduleTime: new Date().toISOString(),
      scheduleTimeError: false,
      showExcludeInput: false,
      excludedStudents: ""
    }
  },
  computed: {
    ...mapGetters("pairing", ["autoJob"]),
    ...mapState({
      rubrics: state => state.rubric.all,
      settings: state => state.assignment.settings,
      scheduledJob: state => state.pairing.autoScheduledJob,
      assignment: state => state.assignment.current
    }),
    rubricName: function() {
      const rubric_id = this.settings.rubric_id
      if (!rubric_id) return "No Rubric"
      let rubric = this.rubrics.find(r => r.id === rubric_id)
      return rubric.hasOwnProperty("name") ? rubric.name : "No Rubric"
    },
    hourAfterDue: function() {
      if (!this.assignment.due_at) return this.assignment.due_at

      let d = new Date(this.assignment.due_at)
      d.setHours(d.getHours() + 1)
      return d
    },
    disableBtns: function() {
      return (
        !this.settings.intra_group_review &&
        (this.pairingError !== "" || this.reviewRounds === 0 || this.isLoading)
      )
    },
    canvasLink: function() {
      return (
        CANVAS_BASE_URL +
        `/courses/${this.$route.params.course_id}/assignments/${
          this.$route.params.assignment_id
        }/edit`
      )
    }
  },
  created() {
    const assignment_id = parseInt(this.$route.params.assignment_id)
    this.$store.dispatch("pairing/getAutoSchedule", assignment_id)
  },
  mounted() {
    const course_id = parseInt(this.$route.params.course_id)
    const assignment_id = parseInt(this.$route.params.assignment_id)
    this.job = this.autoJob(course_id, assignment_id)
    this.isLoading = Boolean(this.job)
  },
  methods: {
    ...mapActions("pairing", [
      "createAutomaticPairing",
      "scheduleAutoPairing",
      "cancelScheduled"
    ]),
    pairStudents: function() {
      this.showConfirmModal = false

      const vm = this
      const course_id = parseInt(vm.$route.params.course_id)
      const assignment_id = parseInt(vm.$route.params.assignment_id)
      let data = {
        course_id,
        assignment_id,
        reviewRounds: vm.reviewRounds,
        excludeDefaulters: vm.excludeDefaulters,
        excludedStudents: vm.excludedStudents
      }
      if (vm.schedule && vm.scheduleType === "custom") {
        data.schedule_time = this.scheduleTime
      }
      vm.pairingError = ""
      vm.isLoading = true
      let pairingCall = vm.schedule
        ? vm.scheduleAutoPairing(data)
        : vm.createAutomaticPairing(data)

      pairingCall
        .then(job => {
          if (vm.schedule) {
            vm.$toasted.success("Automatic pairing scheduled successfully", {
              duration: 5000
            })
            vm.$store.dispatch("pairing/getAutoSchedule", assignment_id)
          } else {
            vm.job = job
          }
        })
        .catch(function(error) {
          vm.isLoading = false

          let errorMessage = null

          try {
            errorMessage = error.response.data.message
          } catch (e) {
            errorMessage = error.statusText
          }

          vm.$toasted.error(errorMessage, { duration: 3000 })
        })
    },
    confirmInputs: function(schedule) {
      if (!this.validateRubric()) return

      // Ensure the number of reviews are set
      if (!this.settings.intra_group_review && this.reviewRounds === 0) {
        this.$toasted.error(
          "You must specify how many assignment should each student grade.",
          { duration: 3000 }
        )
        return
      }
      if (schedule) this.schedule = schedule
      this.showConfirmModal = true
    },
    confirmAndCancelScheduledJob: function() {
      let sure = confirm(
        "Are you sure you want to cancel the scheduled pairing job?"
      )
      if (sure) {
        this.cancelScheduled("auto")
      }
    },
    checkScheduleAndPair: function() {
      if (this.scheduleType === "custom") {
        if (!this.scheduleTime) {
          this.scheduleTimeError = "Invalid time"
          return
        }
        let now = new Date()
        let scheduled = new Date(this.scheduleTime)
        if (scheduled < now) {
          this.scheduleTimeError = "The scheduled time should be in the future"
          return
        }
      }
      this.showScheduleSelector = false
      this.$nextTick(() => this.confirmInputs(true))
    }
  }
}
</script>

<style scoped></style>
