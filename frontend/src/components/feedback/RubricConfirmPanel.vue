<template>
  <div id="rubric_confirm_area">
    <section v-if="grades.length && rubric.criterions">
      <p class="text-primary">Kindly revise the rubric</p>
      <rubric-grade-viewer
        :rubric="rubric"
        :grades="grades"
        @rubric-bottom-visible="rubricBottomReached = true"
      >
      </rubric-grade-viewer>
    </section>

    <button class="btn btn-default" @click="$emit('change-step', 'back')">
      <i class="icon icon-arrow-left" /> I need to make some changes
    </button>

    <button
      class="btn btn-primary ml-2"
      :disabled="disableNextButton"
      @click="$emit('change-step', 'forward')"
    >
      <span v-if="isFinal">Submit Final Feedback</span>
      <span v-else>I have revised the rubric</span>
      <i class="icon icon-arrow-right" />
    </button>
  </div>
</template>

<script>
import RubricGradeViewer from "../rubric/RubricGradeViewer"

export default {
  name: "RubrickConfirmView",
  components: {
    RubricGradeViewer
  },
  props: {
    grades: {
      type: Array,
      required: false,
      default: () => []
    },
    rubric: {
      type: Object,
      required: false,
      default: () => {}
    },
    isFinal: {
      type: Boolean,
      required: true
    }
  },
  data: function() {
    return {
      rubricReviewed: false,
      rubricBottomReached: false
    }
  },
  computed: {
    disableNextButton: function() {
      if (this.grades.length) {
        return !this.rubricBottomReached
      }
      return false
    }
  }
}
</script>

<style scoped></style>
