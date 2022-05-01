<template>
  <div class="panel">
    <div class="panel-header text-center">
      <div class="panel-title h5 mt-10">Assign TA Graders</div>
    </div>
    <div class="panel-body">
      <content-placeholders v-if="tasLoading">
        <content-placeholders-heading />
        <content-placeholders-text :lines="2" />
      </content-placeholders>

      <empty-state
        v-if="!tasLoading && tas.length === 0"
        title="No TAs to assign"
        icon="icon-people"
        message="There are no TAs in the course. Kindly add TAs to the course in Canvas."
      />

      <div v-if="!tasLoading && tas.length > 0">
        <div class="columns">
          <div class="column col-6 col-xs-12 text-center">
            <p>
              Total Students: <span class="chip">{{ studentCount }}</span>
            </p>
          </div>
          <div class="column col-6 col-xs-12 text-center">
            <p>
              TA Assigned:
              <span v-if="countEditable" class="chip">{{ assigned }}</span>
              <span v-else class="chip">{{ preassigned }}</span>

              <i
                v-if="assigned > studentCount"
                class="icon icon-cross text-error"
              ></i>
              <i
                v-if="assigned === studentCount"
                class="icon icon-check text-success"
              ></i>
              <i
                v-if="assigned < studentCount"
                class="icon icon-flag text-warning"
              ></i>
            </p>
          </div>
        </div>
        <table class="table table-striped table-hover table-condensed">
          <thead>
            <tr>
              <th>TA</th>
              <th>Assigned</th>
              <th v-if="reassigning">New Allotment</th>
              <th>Evaluated</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="ta in tas" :key="ta.id">
              <td>{{ ta.name }}</td>
              <td v-if="!countEditable || reassigning">{{ ta.assigned }}</td>
              <td v-if="countEditable">
                <div
                  :class="{
                    'has-icon-left tooltip': localTas[ta.id] < ta.completed
                  }"
                  data-tooltip="Assigned tasks less than completed tasks"
                >
                  <input
                    v-model.number="localTas[ta.id]"
                    class="small-input form-input input-sm"
                    type="number"
                    :min="ta.completed || 0"
                  />
                  <i
                    v-if="localTas[ta.id] < ta.completed"
                    class="form-icon icon icon-flag text-error"
                  ></i>
                </div>
              </td>
              <td>{{ ta.completed }}</td>
            </tr>
            <tr v-if="countEditable">
              <td></td>
              <td v-if="reassigning"></td>
              <td>
                <button class="btn btn-sm" @click="autoDistribute()">
                  Auto Distribute
                </button>
              </td>
              <td></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    <div class="panel-footer">
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

      <button v-if="reassigning" class="btn my-2" @click="reassigning = false">
        Cancel Reassigning
      </button>
      <button
        v-if="countEditable && tas.length > 0"
        class="btn btn-primary m-2"
        :disabled="assigned !== studentCount || assigningTas"
        @click="assignTAGraders()"
      >
        {{ reassigning ? "Re-assign" : "Assign" }} TA Graders
      </button>

      <button
        v-if="preassigned === studentCount && tas.length > 0 && !reassigning"
        class="btn my-2"
        @click="beginReassigning()"
      >
        Change grading distribution
      </button>
    </div>
  </div>
</template>

<script>
import { mapActions, mapState } from "vuex"
import EmptyState from "../ui/EmptyState"
import ProgressBar from "../ui/ProgressBar"

export default {
  name: "AssignTas",
  components: {
    EmptyState,
    ProgressBar
  },
  props: {
    studentCount: {
      type: Number,
      required: true
    }
  },
  data: function() {
    return {
      assigningTas: false,
      localTas: {},
      job: false,
      reassigning: false
    }
  },
  computed: {
    ...mapState("assignment", ["tasLoading", "tas"]),
    assigned: function() {
      return Object.values(this.localTas).reduce(
        (sum, allotted) => sum + Math.abs(allotted),
        0
      )
    },
    preassigned: function() {
      return this.tas.reduce((tot, curr) => tot + curr.assigned, 0)
    },
    countEditable: function() {
      return this.reassigning || this.preassigned < this.studentCount
    }
  },
  created() {
    this.$store.dispatch("assignment/getTAsAllotments", this.$route.params)
  },
  methods: {
    ...mapActions("assignment", ["allotStudentsToTAs"]),
    autoDistribute: function() {
      const self = this
      let allotment = {}
      let assignPerTA = Math.floor(self.studentCount / self.tas.length)
      self.tas.map(ta => (allotment[ta.id] = assignPerTA))

      let remaining = self.studentCount % self.tas.length
      for (let i = 0; i < remaining; i++) {
        allotment[self.tas[i].id]++
      }
      self.localTas = allotment
    },
    clearJob: function() {
      const self = this
      self.job = false
      self.assigningTas = false
      self.$store.dispatch("pairing/getAssignmentPairs", self.$route.params)
      self.$store.dispatch("assignment/getTAsAllotments", self.$route.params)
      self.$emit("pairing-done")
    },
    assignTAGraders: function() {
      const self = this
      const assignment_id = parseInt(self.$route.params.assignment_id)
      const course_id = parseInt(self.$route.params.course_id)
      // If it is an reassignment, ensure no TA is assigned less than already completed values
      for (let i = 0; i < this.tas.length; i++) {
        const ta = this.tas[i]
        if (this.localTas[ta.id] < ta.completed) {
          alert(
            `Cannot reassign tasks for TAs. ${
              ta.name
            } is assigned less tasks than he/she has already completed.`
          )
          return
        }
      }
      self.assigningTas = true
      let allocation = self.tas.map(ta => ({
        ta_id: ta.id,
        student_count: self.localTas[ta.id] || 0
      }))

      self
        .allotStudentsToTAs({ assignment_id, course_id, allocation })
        .then(job => (self.job = job))
        .catch(e => {
          const message =
            e.response.data.message ||
            e.response.data.msg ||
            e.response.statusText
          self.$toasted.error("Failed to assign TAs. " + message, {
            duration: 3000
          })
        })
    },
    beginReassigning: function() {
      // copy the preassigned data to the local TAs data but place restriction based on submitted content
      let allotment = {}
      this.tas.map(ta => (allotment[ta.id] = ta.assigned))
      this.reassigning = true
      this.localTas = allotment
    }
  }
}
</script>

<style scoped>
.small-input {
  max-width: 8em;
}
.table-condensed td,
.table-condensed th {
  padding: 0.1rem 0.1rem;
}
</style>
