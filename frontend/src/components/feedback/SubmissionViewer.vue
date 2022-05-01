<template>
  <div class="column col-12">
    <h2>{{ submission.user.name }}'s Submission</h2>
    <empty-state
      v-if="submission.workflow_state === 'unsubmitted'"
      icon="icon-message"
      title="Assignment not available"
      :message="
        submission.user.name +
          ' has not yet submitted the assignment or has presented it in class.'
      "
      action="Go Back"
      class="mb-2"
      @empty-action="$router.go(-1)"
    />

    <div v-else>
      <div
        v-for="attachment in submission.attachments"
        :key="attachment.filename"
      >
        <pdf
          v-if="attachment.mime_class === 'pdf'"
          :id="'attachment_' + attachment.id"
          :file="attachment.url"
        >
        </pdf>
      </div>

      <div class="py-2 mb-2 panel">
        <div class="panel-body">
          <div
            v-if="submission.submission_type === 'online_text_entry'"
            v-html="submission.body"
          ></div>
          <div v-if="submission.submission_type === 'online_url'">
            <a :href="submission.url">{{ submission.url }}</a>
          </div>
          <div
            v-if="
              submission.submission_type === 'media_recording' ||
                submission.submission_type === 'online_upload'
            "
          >
            <download-grid :submission="submission"></download-grid>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import DownloadGrid from "../ui/DownloadGrid"
import Pdf from "../ui/Pdf"
import EmptyState from "../ui/EmptyState"
import { TimeTracker } from "./timetracker"
import { mapMutations } from "vuex"

export default {
  name: "SubmissionViewer",
  components: {
    DownloadGrid,
    EmptyState,
    Pdf
  },
  mixins: [TimeTracker],
  props: {
    submission: {
      type: Object,
      required: true
    },
    enableTimer: {
      type: Boolean,
      default: false
    }
  },
  data: function() {
    return {
      tEmitMessage: "elapsed-read-time"
    }
  },
  methods: {
    ...mapMutations("feedback", ["updateReadingTime"]),
    emitElapsed: function() {
      this.updateReadingTime(this.getElapsedTime())
    }
  }
}
</script>

<style scoped></style>
