<template>
  <div class="columns">
    <div class="column col-12">
      <div class="panel">
        <div class="panel-header text-center">
          <div class="panel-title h5 mt-10">Pair Students</div>
        </div>
        <nav class="panel-nav">
          <ul class="tab tab-block">
            <li class="tab-item">
              <a
                :class="{ active: currentTab === AUTO_TAB }"
                class="c-hand"
                role="tab"
                @click="setCurrentTab(AUTO_TAB)"
              >
                Automatic
              </a>
            </li>
            <li v-if="!settings.intra_group_review" class="tab-item">
              <a
                :class="{ active: currentTab === CSV_TAB }"
                class="c-hand"
                role="tab"
                @click="setCurrentTab(CSV_TAB)"
              >
                CSV
              </a>
            </li>
            <li v-if="!settings.intra_group_review" class="tab-item">
              <a
                :class="{ active: currentTab === MANUAL_TAB }"
                class="c-hand"
                role="tab"
                @click="setCurrentTab(MANUAL_TAB)"
              >
                Manual
              </a>
            </li>
          </ul>
        </nav>

        <div v-if="jobsLoading" class="panel-body my-2">
          <content-placeholders>
            <content-placeholders-heading />
            <content-placeholders-text :lines="4" />
          </content-placeholders>
        </div>

        <div v-if="!jobsLoading" class="panel-body my-2">
          <automatic-pairing-tab
            v-show="currentTab === AUTO_TAB"
            :rubric-valid="rubricValid"
            :use-rubric="settings.use_rubric"
            @rubric-warning="showRubricWarning"
            @pairing-done="gotoPairingTable()"
          />
          <c-s-v-pairing-tab
            v-show="currentTab === CSV_TAB"
            :rubric-valid="rubricValid"
            :use-rubric="settings.use_rubric"
            @pairing-done="gotoPairingTable()"
            @rubric-warning="showRubricWarning"
          />
          <manual-pairing-tab
            v-show="currentTab === MANUAL_TAB"
            :rubric-valid="rubricValid"
            :use-rubric="settings.use_rubric"
            :students="students"
            @pairing-done="gotoPairingTable()"
            @rubric-warning="showRubricWarning"
          />
        </div>
        <modal
          :title="modalTitle"
          :show-modal="showModal"
          @modalClosed="showModal = false"
        >
          {{ modalContent }}
        </modal>
      </div>
    </div>
    <div class="column col-12 mt-2 pt-2">
      <assign-tas
        :student-count="students.length"
        @pairing-done="gotoPairingTable()"
      ></assign-tas>
    </div>
  </div>
</template>

<script>
import { mapState } from "vuex"
import AutomaticPairingTab from "./AssignmentPairingTabAutomactic"
import CSVPairingTab from "./AssignmentPairingTabCSV"
import ManualPairingTab from "./AssignmentPairingTabManual"
import AssignTas from "./AssignmentAssignTas"
import Modal from "../ui/Modal"

export default {
  name: "PairStudents",
  components: {
    ManualPairingTab,
    CSVPairingTab,
    AutomaticPairingTab,
    AssignTas,
    Modal
  },
  data: function() {
    return {
      currentTab: 0,
      AUTO_TAB: 0,
      CSV_TAB: 1,
      MANUAL_TAB: 2,
      modalTitle: "",
      modalContent: "",
      showModal: false
    }
  },
  computed: {
    ...mapState("assignment", ["settings"]),
    ...mapState("course", ["students"]),
    ...mapState("pairing", ["jobsLoading"]),
    rubricValid: function() {
      return !(this.settings.use_rubric && this.settings.rubric_id === 0)
    }
  },
  created() {
    this.$store.dispatch("pairing/fetchActiveJobs")
  },
  methods: {
    setCurrentTab(tab) {
      this.currentTab = tab
    },
    showRubricWarning() {
      this.modalTitle = "Invalid Rubric"
      this.modalContent = `You have chosen to use a rubric for evaluating the assignments,
          but no rubric has been assigned. Choose a rubric before creating pairings.`
      this.showModal = true
    },
    gotoPairingTable() {
      this.$router.push({
        name: "assignment.pairing-table",
        params: this.$route.params
      })
    }
  }
}
</script>

<style></style>
