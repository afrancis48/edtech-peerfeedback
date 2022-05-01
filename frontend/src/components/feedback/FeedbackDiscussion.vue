<template>
  <section>
    <h2 class="pt-2">{{ title }}</h2>

    <content-placeholders v-if="dataLoading">
      <content-placeholders-heading :img="true" />
      <content-placeholders-text />
    </content-placeholders>

    <div v-if="!dataLoading" class="panel my-2">
      <empty-state
        v-if="!feedbacks.length"
        title="No Feedback !"
        message="No one has submitted a feedback yet"
      ></empty-state>

      <div class="panel-body">
        <feedback-item
          v-for="f in feedbacks"
          :key="f.id"
          :feedback="f"
          @show-rubric-with-grades="onShowRubricWithGrades"
        >
        </feedback-item>
      </div>
    </div>

    <div
      v-if="rubric.hasOwnProperty('criterions')"
      id="modal-id"
      class="modal modal-lg"
      :class="{ active: showRubricModel }"
    >
      <a
        href="#"
        class="modal-overlay"
        aria-label="Close"
        @click="showRubricModel = false"
      ></a>
      <div class="modal-container">
        <div class="modal-header">
          <a
            href="#"
            class="btn btn-clear float-right"
            aria-label="Close"
            @click="showRubricModel = false"
          ></a>
        </div>
        <div class="modal-body">
          <div class="content">
            <rubric-grade-viewer :rubric="rubric" :grades="currentGrades" />
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script>
import FeedbackItem from "./FeedbackItem"
import RubricGradeViewer from "../rubric/RubricGradeViewer"
import EmptyState from "../ui/EmptyState"

import { mapState, mapGetters } from "vuex"

export default {
  name: "FeedbackDiscussion",
  components: {
    FeedbackItem,
    RubricGradeViewer,
    EmptyState
  },
  props: {
    submission: {
      type: Object,
      required: true
    }
  },
  data: function() {
    return {
      currentGrades: [],
      showRubricModel: false,
      dataFetched: false,
      error: "",
      rubric: {}
    }
  },
  computed: {
    ...mapState({
      feedbacks: state => state.feedback.all,
      dataLoading: state => state.feedback.isLoading
    }),
    ...mapGetters("rubric", ["rubricWithId"]),
    title: function() {
      let text = "Feedback"
      if (this.feedbacks.length && this.feedbacks[0].type === "igr") {
        text = `Your Feedback for ${this.feedbacks[0].receiver.name}`
      }
      return text
    }
  },
  watch: {
    dataLoading: function(is, was) {
      // scroll to the location of a particular feedback based on # fragment value in URL
      if (!is && was) {
        const anchor = this.$route.hash
        if (anchor.indexOf("feedback") === -1) return
        this.$nextTick(() => {
          if (anchor && document.querySelector(anchor)) {
            location.href = anchor
          }
        })
      }
    }
  },
  created() {
    this.$store.dispatch("feedback/getSubmissionFeedbacks", this.$route.params)
  },
  methods: {
    onShowRubricWithGrades: function(rubric_id, grades) {
      this.rubric = this.rubricWithId(rubric_id)
      this.currentGrades = grades
      this.showRubricModel = true
    }
  }
}
</script>

<style scoped lang="scss">
.modal.modal-lg .modal-overlay {
  background-color: #e7e9ed;
  opacity: 0.7;
}
.panel-body {
  overflow-y: visible;
  padding: 0;
}
</style>
