<template>
  <div class="popover popover-top">
    <slot></slot>
    <div class="popover-container">
      <div class="card">
        <div class="card-header">
          <h6 class="card-title">{{ user.name }}</h6>
        </div>
        <div class="card-body">
          <reputation
            :feedback-given="user.feedback_given"
            :user-reputation="user.reputation"
            :oldest-review="user.oldest_review"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import Reputation from "./Reputation.vue"

export default {
  name: "ReputationCard",
  components: {
    Reputation
  },
  props: {
    user: {
      type: Object,
      default: function() {
        return {
          name: "Unknown User",
          feedback_given: null,
          reputation: null,
          oldest_review: null
        }
      }
    }
  }
}
</script>

<style scoped></style>
