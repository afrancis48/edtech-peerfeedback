export const PairingMixin = {
  props: {
    rubricValid: Boolean,
    useRubric: Boolean
  },
  data: function() {
    return {
      job: false
    }
  },
  methods: {
    clearJob: function() {
      const vm = this
      vm.isLoading = false
      vm.job = false
      vm.$emit("pairing-done")
    },
    validateRubric: function() {
      const vm = this
      let validity = true
      // Double check pairing without rubric
      if (!vm.useRubric) {
        validity = confirm(
          "Are you sure, you want to carry out pairing without assigning a rubric for evaluation?"
        )
        if (!validity) return false
      }

      // Don't pair if proper assessment rubric is not present
      if (!vm.rubricValid) {
        vm.$emit("rubric-warning")
        return false
      }
      return validity
    }
  }
}
