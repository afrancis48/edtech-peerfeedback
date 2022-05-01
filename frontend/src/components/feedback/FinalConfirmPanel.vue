<template>
  <div class="column col-12 pt-2">
    <h2>Are you sure you want to submit?</h2>

    <div class="toast toast-warning my-2 text-center py-2">
      <octicon name="alert" :scale="10"></octicon>
      <p class="warning-text">
        All submissions are final! This is your last chance to make changes.
      </p>
    </div>

    <div class="my-2 py-2">
      <div class="form-group">
        <label class="form-checkbox">
          <input v-model="dont_show_warning" type="checkbox" />
          <i class="form-icon"></i> I'm aware that my feedback or rubric can not
          be edited after submission. Do not show this message again.
        </label>
      </div>
    </div>

    <button
      class="btn btn-default"
      data-test="fb-confirm-btn"
      @click="$emit('save-feedback', dont_show_warning)"
    >
      Submit final feedback
    </button>

    <button class="btn btn-primary ml-2" @click="$emit('change-step', 'back')">
      <i class="icon icon-arrow-left" /> I need to make some changes
    </button>
  </div>
</template>

<script>
import Octicon from "vue-octicon/components/Octicon"
import "vue-octicon/icons/alert"

export default {
  name: "FinalConfirmPanel",
  components: {
    Octicon
  },
  data: function() {
    return {
      dont_show_warning: false
    }
  }
}
</script>

<style scoped>
.warning-text {
  font-size: 1.3rem;
}
</style>
