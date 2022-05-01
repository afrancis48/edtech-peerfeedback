<template>
  <div class="accordion">
    <input
      :id="id"
      name="accordion-radio"
      type="radio"
      hidden
      :checked="expand"
    />
    <label class="accordion-header c-hand" :for="id">
      <i class="icon icon-arrow-right mr-1"></i> {{ title }}
    </label>
    <div class="accordion-body">
      <span v-if="!pairs.length" class="pl-2 text-error">
        <template v-if="title === 'Feedback from peers'">
          Once your peers finish writing feedback you get email notifications!
        </template>
        <template v-else>
          No Feedback
        </template>
      </span>

      <ul v-if="pairs.length" class="no-style">
        <li v-for="p in pairs" :key="p.id">
          <div class="tile tile-centered">
            <div class="tile-icon">
              <div class="example-tile-icon">
                <avatar
                  v-if="fromUser"
                  :user="p.recipient"
                  size="small"
                ></avatar>
                <avatar v-else :user="p.grader" size="small"></avatar>
              </div>
            </div>
            <div class="tile-content">
              <div class="tile-title">
                <small
                  v-if="p.grader.id === p.creator.id"
                  title="Additional Feedback"
                >
                  <octicon name="diff-added" class="icon"></octicon>
                </small>
                {{ fromUser ? p.recipient.name : p.grader.name }}&nbsp;&nbsp;
                <small v-if="p.task.status === 'COMPLETE'" class="text-success">
                  <octicon name="check" class="icon"></octicon> Complete
                </small>
                <small v-if="p.task.status === 'PENDING' && !p.view_only" class="text-warning">
                  <octicon name="watch" class="icon"></octicon> Pending
                </small>
                <small
                  v-if="p.task.status === 'INPROGRESS'"
                  class="text-primary"
                >
                  <octicon name="zap" class="icon"></octicon> In Draft
                </small>
              </div>
              <small class="tile-subtitle text-gray">
                <span v-if="p.task.status === 'PENDING' && p.task.due_date" >
                  Due on: {{ p.task.due_date | readableDate }}
                </span>
                <span v-if="p.task.status === 'COMPLETE'">
                  Reviewed on: {{ p.task.done_date | readableDate }}
                </span>
              </small>
            </div>
            <div class="tile-action">
              <router-link
                :to="feedbackLink(p)"
                class="btn btn-link"
                target="_blank"
              >
                <span v-if="fromUser && !completed(p) && !p.view_only">
                  <octicon name="comment" class="icon tooltip"></octicon> Give
                  Feedback
                </span>
                <span v-else-if="fromUser && p.view_only">
                  <octicon name="comment" class="icon tooltip"></octicon> View Assignment
                </span>

              </router-link>
            </div>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
import Avatar from "../ui/Avatar"
import Octicon from "vue-octicon/components/Octicon"
import "vue-octicon/icons/comment"
import "vue-octicon/icons/comment-discussion"
import "vue-octicon/icons/check"
import "vue-octicon/icons/zap"
import "vue-octicon/icons/watch"
import "vue-octicon/icons/diff-added"

export default {
  name: "AssignmentFeedbackAccordion",
  components: {
    Avatar,
    Octicon
  },
  props: {
    pairs: {
      type: Array,
      required: true
    },
    title: {
      type: String,
      default: "Feedback"
    },
    id: {
      type: String,
      default: ""
    },
    fromUser: {
      type: Boolean,
      default: false
    },
    expand: {
      type: Boolean,
      default: false
    }
  },
  methods: {
    feedbackLink: function(pairing) {
      return {
        name: "give-feedback",
        params: {
          course_id: pairing.course_id,
          assignment_id: pairing.assignment_id,
          user_id: pairing.recipient.id,
          view_only: pairing.view_only
        }
      }
    },
    completed: function(p) {
      return p.task.status === "COMPLETE"
    }
  }
}
</script>

<style scoped>
.no-style {
  list-style: none;
}
</style>
