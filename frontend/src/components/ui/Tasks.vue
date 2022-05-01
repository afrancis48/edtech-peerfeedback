<template>
  <section id="tasklist">
    <div v-for="task in incompleteTasks" :key="'task_' + task.id" class="task">
      <div v-if="task.archiving" class="tile loading"></div>

      <div v-else class="tile tile-centered">
        <div class="tile-icon">
          <reputation-card :user="task.pairing.recipient">
            <avatar :user="task.pairing.recipient"></avatar>
          </reputation-card>
        </div>
        <div class="tile-content">
          <div class="tile-title">
            <router-link
              :to="giveFeedbackLink(task)"
              target="_blank"
              class="text-dark"
            >
              <span v-if="task.pairing.type === 'igr'">
                Give anonymous feedback to {{ task.pairing.recipient.name }}
              </span>
              <span v-else>
                Review {{ task.pairing.recipient.name }}'s assignment
              </span>
            </router-link>
            <span
              v-if="task.pairing.type === 'TA'"
              class="label label-secondary"
            >
              TA
            </span>
          </div>
          <div class="tile-subtitle text-gray">
            <small>{{ task.course_name }} · {{ task.assignment_name }}</small>
          </div>
          <span v-if="task.due_date" class="d-block">
            <small>
              <octicon name="clock" class="icon"></octicon>
              {{ task.due_date | readableDate }}
            </small>
          </span>
        </div>
        <div class="tile-action">
          <router-link
            :to="giveFeedbackLink(task)"
            class="btn btn-link tooltip"
            target="_blank"
            data-tooltip="Give Feedback"
            data-test="give-feedback"
          >
            <octicon name="comment-discussion" class="icon" />
          </router-link>
          <button
            class="btn btn-link tooltip"
            data-tooltip="Archive Task"
            @click="confirmArchiveTask(task)"
          >
            <octicon name="archive" class="icon text-gray"></octicon>
          </button>
        </div>
      </div>
    </div>

    <confirm-modal
      title="Are you sure you want to archive this task?"
      confirm="Archive Task"
      reject="Cancel"
      :show-modal="showArchiveConfirmation"
      size="medium"
      @confirmed="archive()"
      @rejected="showArchiveConfirmation = false"
    >
      <table class="table">
        <tbody v-if="archivingTask">
          <tr>
            <th>Course</th>
            <td>{{ archivingTask.course_name }}</td>
          </tr>
          <tr>
            <th v-if="archivingTask.pairing.type === 'igr'">Task</th>
            <th v-else>Assignment</th>
            <td>{{ archivingTask.assignment_name }}</td>
          </tr>
          <tr>
            <th v-if="archivingTask.pairing.type === 'igr'">Feedback for</th>
            <th v-else>Submission By</th>
            <td>
              <avatar :user="archivingTask.pairing.recipient"></avatar>
              {{ archivingTask.pairing.recipient.name }}
            </td>
          </tr>
          <tr v-if="archivingTask.due_at">
            <th>Due at</th>
            <td>{{ archivingTask.due_at | readableDate }}</td>
          </tr>
        </tbody>
      </table>
      <div class="toast">
        <octicon name="alert" class="icon"></octicon> Archiving can not be
        undone.
      </div>
    </confirm-modal>
  </section>
</template>

<script>
import Octicon from "vue-octicon/components/Octicon"
import "vue-octicon/icons/comment-discussion"
import "vue-octicon/icons/clock"
import "vue-octicon/icons/alert"
import Avatar from "./Avatar"
import ConfirmModal from "./ConfirmModal"
import { mapActions } from "vuex"
import ReputationCard from "./ReputationCard"

Octicon.register({
  archive: {
    width: 14,
    height: 16,
    d:
      "M13 2H1v2h12V2zM0 4a1 1 0 0 0 1 1v9a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1V5a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1H1a1 1 0 0 0-1 1v2zm2 1h10v9H2V5zm2 3h6V7H4v1z"
  }
})

export default {
  name: "Tasks",
  components: {
    Octicon,
    Avatar,
    ConfirmModal,
    ReputationCard
  },
  props: {
    incompleteTasks: {
      type: Array,
      required: true
    }
  },
  data: function() {
    return {
      showArchiveConfirmation: false,
      archivingTask: null
    }
  },
  methods: {
    ...mapActions("tasks", ["archiveTask"]),
    giveFeedbackLink: function(task) {
      return {
        name: "give-feedback",
        params: {
          course_id: task.course_id,
          assignment_id: task.assignment_id,
          user_id: task.pairing.recipient.id,
          view_only: task.pairing.view_only
        }
      }
    },
    confirmArchiveTask: function(task) {
      this.archivingTask = task
      this.showArchiveConfirmation = true
    },
    archive: function() {
      this.$store.dispatch("task/archiveTask", this.archivingTask.id)
      this.showArchiveConfirmation = false
      this.archivingTask = null
    }
  }
}
</script>

<style scoped>
.task {
  border: 1px solid #f0f1f4;
  border-radius: 0.2rem;
  margin-bottom: 0.1rem;
}
.task > .tile {
  margin: 0.4rem;
}
</style>
