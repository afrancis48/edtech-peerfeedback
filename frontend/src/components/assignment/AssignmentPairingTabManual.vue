<template>
  <div>
    <div class="form-group">
      <label class="form-label" for="graderEmail">Grader Email</label>
      <user-selector
        id="graderEmail"
        v-model="grader"
        :users="students"
        placeholder="grader@example.edu"
      ></user-selector>
    </div>
    <div class="form-group">
      <label class="form-label" for="recipientEmail">Recipient Email</label>
      <user-selector
        id="recipientEmail"
        v-model="recipient"
        :users="students"
        placeholder="recipient@example.edu"
      ></user-selector>

      <span
        :v-show="pairingError !== ''"
        class="pf-inline pull-right pf-centered-bottom pf-pad-top10"
      >
        {{ pairingError }}
      </span>
    </div>

    <div class="form-group">
      <button
        data-test="manual-pair-btn"
        :disabled="pairingError !== '' || !grader || !recipient"
        :class="{ loading: isLoading }"
        class="btn btn-primary btn-block"
        @click="pairStudents"
      >
        Pair Students
      </button>
    </div>
  </div>
</template>

<script>
import { mapActions } from "vuex"
import UserSelector from "../ui/UserSelector"
import { PairingMixin } from "./mixins"

export default {
  name: "ManualPairing",
  components: {
    UserSelector
  },
  mixins: [PairingMixin],
  props: {
    students: {
      type: Array,
      required: true
    },
    rubricValid: Boolean,
    useRubric: Boolean
  },
  data: () => {
    return {
      isLoading: false,
      pairingError: "",
      grader: "",
      recipient: "",
      suggestionAttribute: "email"
    }
  },
  methods: {
    ...mapActions("pairing", ["createManualPairing"]),
    pairStudents: function() {
      const self = this
      const toast = self.$toasted
      self.pairingError = ""

      if (!self.validateRubric()) return

      let data = {
        course_id: parseInt(self.$route.params.course_id),
        assignment_id: parseInt(self.$route.params.assignment_id),
        grader: self.grader.id,
        recipient: self.recipient.id
      }

      self.isLoading = true
      self
        .createManualPairing(data)
        .then(() => {
          toast.success("New pair has been created. Loading pairs ...", {
            duration: 3000
          })
          self.isLoading = false
          self.$emit("pairing-done")
        })
        .catch(function(error) {
          self.isLoading = false
          if (error.response.data.hasOwnProperty("message")) {
            toast.error(error.response.data.message, { duration: 5000 })
          } else {
            toast.error(
              `${error.response.status} ${error.response.statusText}`,
              { duration: 5000 }
            )
          }
        })
    }
  }
}
</script>

<style scoped></style>
