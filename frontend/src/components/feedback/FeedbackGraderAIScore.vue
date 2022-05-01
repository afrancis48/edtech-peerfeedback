<template>
  <div class="py-2 mt-2 d-block">
    <p>
      <span class="tooltip tooltip-right" data-tooltip="AI feedback evaluation">
        <octicon name="question" class="text-gray" scale="0.8"></octicon>
      </span>
      Quality Rating: <span v-if="score === -1" class="chip">Unknown</span>
      <span v-if="score === 0">&#x1f44e;</span>
      <span v-else-if="score === 1">&#x1F610;</span>
      <span v-else-if="score === 2">&#x1f44d;</span> Confidence:
      <span v-if="confidence === -1" class="chip">Unknown</span>
      <span v-else>{{ confidence * 100 }}%</span>
      <a
        class="btn-link float-right p-0 c-hand tooltip tooltip-left"
        data-tooltip="AI feedback evaluation"
        :disabled="!loadingScore"
        @click="getAIQualityScore(value)"
      >
        {{ loadingScore ? "Checking ..." : "Check Quality" }}
      </a>
    </p>
  </div>
</template>

<script>
import { mapState, mapActions } from "vuex"
import Octicon from "vue-octicon/components/Octicon"
import "vue-octicon/icons/question"

export default {
  name: "FeedbackGraderAIScore",
  components: {
    Octicon
  },
  props: {
    value: {
      type: String,
      default: ""
    }
  },
  computed: {
    ...mapState({
      score: state => state.feedback.aiScore,
      confidence: state => state.feedback.aiConfidence,
      loadingScore: state => state.feedback.aiScoreLoading
    })
  },
  created() {
    this.$store.commit("feedback/resetAIValues")
  },
  methods: {
    ...mapActions("feedback", ["getAIQualityScore"])
  }
}
</script>

<style scoped></style>
