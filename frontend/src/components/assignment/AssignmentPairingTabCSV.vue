<template>
  <div>
    <div class="form-group">
      <label class="form-label">Grader Type</label>
      <label class="form-radio form-inline">
        <input
          id="grader_student"
          v-model="graderType"
          type="radio"
          name="grader_type"
          value="STUDENT"
        />
        <i class="form-icon"></i> <small>Student</small>
      </label>
      <label class="form-radio form-inline">
        <input
          id="grader_ta"
          v-model="graderType"
          type="radio"
          name="grader_type"
          value="TA"
        />
        <i class="form-icon"></i> <small>TA</small>
      </label>
    </div>
    <div
      v-if="dragAndDropEnabled"
      id="drop_area"
      class="form-group"
      @drop="handleFileDrop"
      @dragover="handleDragOver"
    >
      <input id="drop_file_input" type="file" @change="loadCSV" />
      <label for="drop_file_input">
        <strong>Choose CSV a file</strong> or Drag & Drop it here
      </label>
    </div>
    <div
      v-if="dragAndDropEnabled"
      class="divider text-center"
      data-content="OR"
    ></div>
    <div class="form-group">
      <label class="form-label" for="bulkPairGrader">
        Specify student pairings via CSV
      </label>
      <textarea
        id="bulkPairGrader"
        v-model="csv"
        class="form-input"
        placeholder="Grader GT username, Recipient #1 GT username, Recipient #2 GT username..."
        rows="3"
      >
      </textarea>
      <div v-if="pairingError" class="text-error my-2">{{ pairingError }}</div>
    </div>
    <div class="form-group">
      <label class="form-checkbox">
        <input v-model="allowMissing" type="checkbox" />
        <i class="form-icon"></i> Allow students without a submission to be
        paired
      </label>
    </div>
    <div v-if="scheduledJob" class="column col-12">
      <p class="bg-gray p-2">
        <small>
          A set of students have been scheduled to be paired on
          <em>{{ scheduledJob.date | readableDate }}</em>
        </small>
      </p>
    </div>
    <div class="form-group">
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
        class="btn btn-error mt-2"
        @click="confirmAndCancelSchedule"
      >
        Cancel Scheduled Pairing
      </button>
      <button
        v-else
        class="btn btn-default mt-2"
        :disabled="!csv.length || isLoading"
        @click="showScheduleSelector = true"
      >
        Schedule Pairing
      </button>
      <button
        data-test="csv-pair-btn"
        class="btn btn-primary mt-2 ml-2 float-right"
        :disabled="!csv.length || isLoading"
        @click="pairStudents(false)"
      >
        Pair Now
      </button>
    </div>

    <div
      id="csv-date-selector"
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
          </div>
        </div>
        <div class="modal-footer">
          <button
            class="btn btn-secondary"
            @click="showScheduleSelector = false"
          >
            Cancel
          </button>
          <button class="btn btn-primary ml-2" @click="schedulePair">
            Schedule Pairing
          </button>
        </div>
      </div>
    </div>

    <modal
      :title="modalTitle"
      :show-modal="showModal"
      @modalClosed="showModal = false"
    >
      {{ modalContent }}
    </modal>
  </div>
</template>

<script>
import { mapActions, mapState } from "vuex"
import Modal from "../ui/Modal"
import ProgressBar from "../ui/ProgressBar"
import { PairingMixin } from "./mixins"
import { Datetime } from "vue-datetime"
import "vue-datetime/dist/vue-datetime.min.css"

import { parsePairingCSV } from "../../utils/index"

export default {
  name: "CSVPairingTab",
  components: {
    Modal,
    ProgressBar,
    Datetime
  },
  mixins: [PairingMixin],
  data: function() {
    return {
      pairingError: "",
      isLoading: false,
      csv: "",
      modalTitle: "",
      modalContent: "",
      showModal: false,
      allowMissing: false,
      graderType: "STUDENT",
      showScheduleSelector: false,
      scheduleTimeError: "",
      scheduleTime: new Date().toISOString()
    }
  },
  computed: {
    ...mapState("pairing", ["csvJob"]),
    ...mapState("course", ["students", "tas"]),
    ...mapState({
      scheduledJob: state => state.pairing.csvScheduledJob
    }),
    dragAndDropEnabled: function() {
      const div = document.createElement("div")
      return (
        ("draggable" in div || ("ondragstart" in div && "ondrop" in div)) &&
        "FormData" in window &&
        "FileReader" in window
      )
    }
  },
  created() {
    const course_id = parseInt(this.$route.params.course_id)
    const assignment_id = parseInt(this.$route.params.assignment_id)
    this.$store.dispatch("pairing/getCSVSchedule", assignment_id)
    this.$store.dispatch("course/getTAs", course_id)
  },
  mounted() {
    this.job = this.csvJob
    this.isLoading = Boolean(this.csvJob)
  },
  methods: {
    ...mapActions("pairing", [
      "createCSVPairing",
      "scheduleCSVPairing",
      "cancelScheduled"
    ]),
    invalidUserIds: function({ pairs }) {
      const userIDs = this.students
        .map(s => s.user_id)
        .concat(this.tas.map(t => t.user_id))
      console.log(userIDs)
      let invalid = []
      pairs.forEach(function(pair) {
        if (userIDs.indexOf(pair.grader) === -1) {
          invalid.push(pair.grader)
        }
        pair.recipients.forEach(function(user) {
          if (userIDs.indexOf(user) === -1) {
            invalid.push(user)
          }
        })
      })
      return invalid
    },
    pairStudents: function(schedule) {
      const vm = this
      const toast = vm.$toasted
      vm.pairingError = ""
      const course_id = parseInt(vm.$route.params.course_id)
      const assignment_id = parseInt(vm.$route.params.assignment_id)

      if (!vm.validateRubric()) return

      const pairingMap = parsePairingCSV(vm.csv)
      if (pairingMap.errors.length > 0) {
        vm.modalTitle =
          "Errors were found in the input CSV. Fix them and try again"
        vm.modalContent = pairingMap.errors.join(" ")
        vm.showModal = true
        vm.isLoading = false
        return
      }
      const invalids = this.invalidUserIds(pairingMap)

      if (invalids.length) {
        vm.pairingError = "The following users where not found in the course: "
        vm.pairingError += invalids.join(", ")
        return
      }

      // data for pairing mode
      let data = {
        course_id,
        assignment_id,
        pairs: pairingMap.pairs,
        allowMissing: vm.allowMissing,
        graderType: vm.graderType
      }

      if (schedule) {
        data.schedule_time = this.scheduleTime
      }

      vm.isLoading = true
      let pairingCall = schedule
        ? vm.scheduleCSVPairing(data)
        : vm.createCSVPairing(data)

      pairingCall
        .then(job => {
          if (schedule) {
            vm.$toasted.success("CSV Pairing scheduled successfully", {
              duration: 5000
            })
            vm.$store.dispatch("pairing/getCSVSchedule", assignment_id)
          } else {
            vm.job = job
          }
        })
        .catch(error => {
          let msg = "CSV Pairing request failed."
          if (error.response) {
            msg += error.response.statusText
            if (error.response.data.hasOwnProperty("message")) {
              msg = error.response.data.message
            }
          }
          vm.isLoading = false
          toast.error(msg, { duration: 5000 })
        })
    },
    confirmAndCancelSchedule() {
      let sure = confirm(
        "Are you sure you want to the cancel the scheduled pairing?"
      )
      if (sure) {
        this.cancelScheduled("csv")
      }
    },
    schedulePair() {
      if (!this.scheduleTime) {
        this.scheduleTimeError = "Invalid time"
        return
      }

      let now = new Date()
      let scheduled = new Date(this.scheduleTime)
      if (scheduled < now) {
        this.scheduleTimeError = "The scheduled times should be in the future"
        return
      }

      this.showScheduleSelector = false
      this.$nextTick(() => this.pairStudents(true))
    },
    populateCSVTextFromFile(file) {
      if (!file || file.type !== "text/csv") {
        this.$toasted.error("Kindly select a CSV file.", { duration: 3000 })
        return
      }
      const vm = this
      const reader = new FileReader()
      reader.onload = e => {
        vm.csv = e.target.result
      }
      reader.readAsText(file)
    },
    handleFileDrop(e) {
      e.preventDefault()
      this.populateCSVTextFromFile(e.dataTransfer.files[0])
    },
    handleDragOver(e) {
      e.preventDefault()
      e.dataTransfer.dropEffect = "copy"
    },
    loadCSV(e) {
      this.populateCSVTextFromFile(e.target.files[0])
    }
  }
}
</script>

<style scoped>
#drop_area {
  display: block;
  width: 100%;
  height: 10rem;
  background-color: #fafaff;
  padding-top: 4rem;
  text-align: center;
  outline: 2px dashed #bbbbef;
  outline-offset: -10px;
}
#drop_file_input {
  width: 0px;
  height: 0px;
  opacity: 0;
  overflow: hidden;
  position: absolute;
  z-index: -1;
}

#drop_area > label {
  cursor: pointer;
}
#drop_area:hover > label > strong {
  color: #5755d9;
}
</style>
