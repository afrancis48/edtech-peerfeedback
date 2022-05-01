<template>
  <div class="columns page">
    <div class="column col-6 col-sm-12">
      <h2>Active Courses</h2>
      <courses :courses="activeCourses"></courses>
    </div>
    <div class="column col-6 col-sm-12">
      <h2>Archived Courses</h2>
      <courses :courses="inactiveCourses"></courses>
    </div>
  </div>
</template>

<script>
import Courses from "../components/course/Courses"
import { mapState, mapGetters } from "vuex"

export default {
  name: "AllCourses",
  components: {
    Courses
  },
  computed: {
    ...mapState({
      loading: state => state.course.isLoading
    }),
    ...mapGetters("course", ["activeCourses", "inactiveCourses"])
  }
}
</script>

<style scoped></style>
