<template>
  <ul class="step feedback-steps">
    <li
      class="step-item"
      :class="{ active: currentStep === 'grading' }"
      @click="setStep('grading')"
    >
      <a
        href="#"
        :class="{
          'default-cursor': !stepAvailable('grading')
        }"
      >
        Write feedback and grade
      </a>
    </li>
    <li
      class="step-item"
      :class="{ active: currentStep === 'revisingFeedback' }"
      @click="setStep('revisingFeedback')"
    >
      <a
        href="#"
        :class="{
          'default-cursor': !stepAvailable('revisingFeedback')
        }"
      >
        Revise feedback
      </a>
    </li>
    <li
      v-if="rubricAvailable"
      class="step-item"
      :class="{ active: currentStep === 'revisingRubric' }"
      @click="setStep('revisingRubric')"
    >
      <a
        href="#"
        :class="{
          'default-cursor': !stepAvailable('revisingRubric')
        }"
      >
        Revise rubric
      </a>
    </li>
    <li
      class="step-item"
      :class="{ active: currentStep === 'finalConfirm' }"
      @click="setStep('finalConfirm')"
    >
      <a
        href="#"
        :class="{
          'default-cursor': !stepAvailable('finalConfirm')
        }"
      >
        Submission
      </a>
    </li>
  </ul>
</template>

<script>
export default {
  name: "FeedbackSteps",
  props: {
    rubricAvailable: {
      type: Boolean,
      required: true,
      default: false
    },
    currentStep: {
      type: String,
      required: true,
      default: "grading"
    }
  },
  methods: {
    stepAvailable(step) {
      if (this.currentStep === "finalConfirm") return true
      else if (this.currentStep === "revisingRubric") {
        if (step != "finalConfirm") return true
        else return false
      } else if (this.currentStep === "revisingFeedback") {
        if (step != "revisingRubric" && step != "finalConfirm") return true
        else return false
      } else {
        if (step === "grading") return true
        else return false
      }
    },
    setStep(stepName) {
      if (this.stepAvailable(stepName)) {
        this.$emit("change-step", stepName)
      }
    }
  }
}
</script>

<style>
.default-cursor {
  cursor: default;
}
.feedback-steps {
  margin-top: 1.2em;
}
</style>
