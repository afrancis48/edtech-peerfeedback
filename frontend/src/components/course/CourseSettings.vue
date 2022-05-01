<template>
  <section class="page">
    <h2>Course-wide Settings</h2>
    <div class="form-group columns">
      <div class="column col-7">
        <label class="form-label" for="maxReviews">
          Maximum extra review tasks per student
        </label>
      </div>
      <div class="column col-5">
        <input
          id="maxReviews"
          v-model="max_reviews"
          type="number"
          min="0"
          class="form-input"
          :disabled="isDisabled"
        />
      </div>
    </div>
    <button
      class="btn btn-primary float-right"
      data-test="save-button"
      :disabled="isDisabled"
      @click="updateMaxReviews"
    >
      Save
    </button>
  </section>
</template>
<script>
import CourseAPI from "../../api/course.js"

export default {
  name: "CourseSettings",
  components: {},
  data: function() {
    return {
      max_reviews: 0,
      isDisabled: false
    }
  },
  methods: {
    updateMaxReviews: function() {
      const course_id = parseInt(this.$route.params.id)
      const data = { course_id: course_id, max_reviews: this.max_reviews }
      this.isDisabled = true
      CourseAPI.updateCourseSettings(
        data,
        response => {
          this.$toasted.show(response.message, {
            duration: 3000,
            type: "success"
          })
          this.isDisabled = false
        },
        err => {
          console.log(err.response)
          this.$toasted.show(err.response.data.message, {
            duration: 3000,
            type: "error"
          })
          this.isDisabled = false
        }
      )
    }
  }
}
</script>
<style scoped></style>
