<template>
  <div>
    <p>
      <strong>Feedback Given:</strong>
      {{ feedbackGiven || "N/A" }} <br />
      <span
        class="tooltip mx-1"
        data-tooltip="From feedback on feedback evaluations"
      >
        <octicon name="question" class="text-gray" scale="0.8" />
      </span>
      <strong>Reputation:</strong> {{ reputation }}<br />
      <strong>Reviewer since:</strong>
      {{ oldestReview | shortDate }}
    </p>
    <small>
      <p class="text-gray">
        Values are not always up to date. Profiles are updated every evening.
      </p>
    </small>
  </div>
</template>

<script>
import Octicon from "vue-octicon/components/Octicon"
import "vue-octicon/icons/question"

export default {
  name: "Reputation",
  components: {
    Octicon
  },
  props: {
    feedbackGiven: Number,
    userReputation: Number,
    oldestReview: String
  },
  computed: {
    reputation : function () {
      if (this.userReputation) {
        let score = (this.userReputation/6) * 100
        return score.toFixed(2) + "%"
      }

      return "N/A"
    }
  }
}
</script>

<style scoped></style>
