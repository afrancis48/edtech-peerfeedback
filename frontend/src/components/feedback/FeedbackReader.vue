<template>
  <section class="columns" style="min-width: 100%">
    <submission-viewer
      v-if="!settings.intra_group_review"
      :submission="submission"
    ></submission-viewer>

    <div id="feedbacks_area" class="column col-12">
      <feedback-discussion :submission="submission"></feedback-discussion>
    </div>

    <div
      v-if="!settings.intra_group_review"
      id="comments_area"
      class="column col-12"
    >
      <comment-thread :submission-id="submission.id"></comment-thread>
    </div>
  </section>
</template>

<script>
import SubmissionViewer from "./SubmissionViewer"
import FeedbackDiscussion from "./FeedbackDiscussion"
import CommentThread from "./CommentThread"
import { mapState } from "vuex"

export default {
  name: "FeedbackReader",
  components: {
    SubmissionViewer,
    FeedbackDiscussion,
    CommentThread
  },
  props: {
    submission: {
      type: Object,
      required: true
    }
  },
  computed: {
    ...mapState("assignment", ["settings"])
  }
}
</script>

<style scoped></style>
