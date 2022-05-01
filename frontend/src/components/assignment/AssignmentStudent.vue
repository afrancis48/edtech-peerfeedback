<template>
  <main class="page">
    <div v-if="pairsLoading" class="columns">
      <div class="column col-6 col-md-12">
        <content-placeholders>
          <content-placeholders-heading />
          <content-placeholders-text />
        </content-placeholders>
      </div>
      <div v-if="settingsLoading" class="column col-6 col-md-12">
        <content-placeholders>
          <content-placeholders-heading />
          <content-placeholders-text />
        </content-placeholders>
      </div>
    </div>

    <div v-if="!pairsLoading" class="columns">
      <div class="column col-6 col-md-12 pb-2">
        <h2>View Feedback</h2>
        <feedback-accordion
          id="accordion-1"
          :pairs="recipientPairs"
          title="Feedback from peers"
          :expand="true"
        >
        </feedback-accordion>
        <feedback-accordion
          id="accordion-2"
          :pairs="TAPairs"
          title="Feedback from TAs"
        >
        </feedback-accordion>
        <feedback-accordion
          id="accordion-3"
          :pairs="gradingPairs"
          title="Your feedback to others"
          :from-user="true"
        >
        </feedback-accordion>
      </div>

      <div class="divider col-sm-12 py-2"></div>

      <empty-state
        v-if="settingsNotExist"
        class="column col-6 col-sm-12"
        title="Assignment not initialized!"
        message="The assignment specs doesn't exist in the app. Ask you professor to setup the course."
      >
      </empty-state>

      <div class="column col-6 col-md-12">
        <div v-if="allowExtraPairing">
          <h2>Give Additional Feedback</h2>
          <div v-if="extrasGiven >= settings.max_reviews">
            <p class="text-gray text-center">
              <octicon
                name="issue-closed"
                class="icon text-warning"
                scale="1.5"
              ></octicon>
              You have reached the limit of
              <span class="chip">{{ settings.max_reviews }}</span> extra reviews
              per student. You cannot give any more extra reviews.
            </p>
          </div>
          <div v-else>
            <p class="text-gray">
              You have obtained <span class="chip">{{ extrasGiven }}</span> out
              of <span class="chip">{{ settings.max_reviews }}</span> allowed
              extra review tasks.
            </p>
            <assignment-select-peer
              :assignment="assignment"
            ></assignment-select-peer>
          </div>
        </div>
        <div
          v-if="!extraLoading && settings.allow_student_pairing"
          class="more-feedback"
        >
          <h2>More Feedback for your assignment</h2>
          <p class="text-gray">
            Ask to receive more feedback on your own assignment than what you
            have received so far.
          </p>
          <button
            v-if="!extraFeedback.active"
            class="btn btn-default"
            @click="requestExtra()"
          >
            Get Feedback
          </button>
          <div v-if="extraFeedback.active" class="message bg-gray text-primary">
            <h6><octicon class="icon" name="verified"></octicon> Requested</h6>
            <p>
              Your request for extra feedback on this assignment is registered.
              You will be able to raise another request once the current request
              is fulfilled.
            </p>
            <button
              class="btn btn-secondary"
              :class="{ loading: deletingExtra }"
              @click="deleteExtraRequest()"
            >
              Cancel Request
            </button>
          </div>
        </div>
      </div>

      <div class="column col-6 col-md-12">
        <div v-if="allowViewAssignments">
          <h2>View Other Assignments</h2>
          <feedback-accordion
            id="accordion-4"
            :pairs="viewPairs"
            title="View Feedback"
            :from-user="true"
          >
          </feedback-accordion>
          <div>
            <assignment-view-peer
              :assignment="assignment"
            ></assignment-view-peer>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>

<script>
import { mapState, mapGetters, mapActions } from "vuex"
import Octicon from "vue-octicon/components/Octicon"
import "vue-octicon/icons/verified"
import "vue-octicon/icons/issue-closed"

import AssignmentFeedbackAccordion from "./AssignmentFeedbackAccordion"
import AssignmentSelectPeer from "./AssignmentSelectPeer"
import AssignmentViewPeer from "./AssignmentViewPeer"
import EmptyState from "../ui/EmptyState"

export default {
  name: "AssignmentStudent",
  components: {
    FeedbackAccordion: AssignmentFeedbackAccordion,
    AssignmentSelectPeer,
    AssignmentViewPeer,
    Octicon,
    EmptyState
  },
  props: {
    course: {
      type: Object,
      required: true
    },
    assignment: {
      type: Object,
      required: true
    }
  },
  computed: {
    ...mapState({
      extraFeedback: state => state.feedback.extra,
      extraLoading: state => state.feedback.extraLoading,
      extrasGiven: state => state.feedback.extrasGiven,
      settingsNotExist: state => state.feedback.settingsNotExist,
      pairs: state => state.pairing.all,
      pairsLoading: state => state.pairing.isLoading,
      deletingExtra: state => state.feedback.deletingExtra
    }),
    ...mapGetters("user", ["currentUser"]),
    ...mapState("assignment", ["settings", "settingsLoading"]),
    gradingPairs: function() {
      return this.pairs.filter(
        p =>
          (p.type === "student" || p.type === "igr") &&
          p.grader.id === this.currentUser.id &&
          p.task.status !== "ARCHIVED" &&
          p.view_only == false
      )
    },
    viewPairs: function() {
      return this.pairs.filter(
          p =>
              (p.type === "student" || p.type === "igr") &&
              p.grader.id === this.currentUser.id &&
              p.view_only == true
      )
    },
    recipientPairs: function() {
      return this.pairs.filter(
        p =>
          (p.type === "student" || p.type === "igr") &&
          p.recipient.id === this.currentUser.id &&
          p.task.status !== "ARCHIVED"
      )
    },
    TAPairs: function() {
      return this.pairs.filter(
        p => p.type === "TA" && p.task.status === "COMPLETE"
      )
    },
    allowExtraPairing: function() {
      let due = new Date(this.assignment.due_at)
      return (
        !this.settingsNotExist &&
        !this.settingsLoading &&
        this.settings.allow_student_pairing &&
        due < new Date()
      )
    },
    allowViewAssignments: function() {
      return (
        !this.settingsNotExist &&
        !this.settingsLoading &&
        this.settings.allow_view_peer_assignments
      )
    }
  },
  created() {
    this.$store.dispatch("assignment/loadSettings", this.$route.params)
    this.$store.dispatch("pairing/getMyAssignmentPairs", this.$route.params)
    this.$store.dispatch("feedback/getExtraFeedbackRequest", this.$route.params)
    this.$store.dispatch("feedback/getExtraFeedbackGiven", this.$route.params)
  },
  methods: {
    ...mapActions("feedback", ["deleteExtraRequest"]),
    requestExtra: function() {
      this.$store.dispatch("feedback/requestExtraFeedback", this.$route.params)
    }
  }
}
</script>

<style scoped>
.message {
  padding: 1rem;
  border-radius: 0.2rem;
}

.more-feedback {
  margin-top: 2rem;
}
</style>
