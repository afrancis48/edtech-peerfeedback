<template>
  <div id="feedback_confirm_area">
    <section>
      <p class="text-primary">Kindly revise your feedback</p>
      <div class="py-2 mb-2" v-html="feedbackHTML"></div>
    </section>

    <button class="btn btn-default" @click="$emit('change-step', 'back')">
      <i class="icon icon-arrow-left" />
      I need to make some changes
    </button>

    <button
      class="btn btn-primary ml-2"
      @click="$emit('change-step', 'forward')"
    >
      <span v-if="isFinal">Submit Final Feedback</span>
      <span v-else>I have revised my feedback</span>
      <i class="icon icon-arrow-right" />
    </button>
  </div>
</template>

<script>
import marked from "marked"

export default {
  name: "FeedbackConfirmView",
  props: {
    feedback: {
      type: String,
      required: true
    },
    isFinal: {
      type: Boolean,
      required: true
    }
  },
  computed: {
    feedbackHTML: function() {
      return marked(this.feedback)
    }
  }
}
</script>

<style scoped></style>
