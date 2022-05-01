<template>
  <main class="page">
    <content-placeholders
      v-if="courseLoading || assignmentLoading"
      :rounded="true"
    >
      <content-placeholders-heading />
      <content-placeholders-img />
      <content-placeholders-text />
    </content-placeholders>

    <div v-if="dataLoaded">
      <assignment-student
        v-if="role === 'student'"
        :course="course"
        :assignment="assignment"
      />
      <assignment-professor
        v-if="role === 'teacher' || role === 'ta'"
        :course="course"
        :assignment="assignment"
      />
    </div>
  </main>
</template>

<script>
import { mapState, mapGetters } from "vuex"

import AssignmentProfessor from "../components/assignment/AssignmentProfessor"
import AssignmentStudent from "../components/assignment/AssignmentStudent"

export default {
  name: "Assignment",
  components: {
    AssignmentProfessor,
    AssignmentStudent
  },
  computed: {
    ...mapState({
      courseLoading: state => state.course.isLoading,
      course: state => state.course.current,
      assignmentLoading: state => state.assignment.isLoading,
      assignment: state => state.assignment.current
    }),
    ...mapGetters("course", ["role"]),
    dataLoaded: function() {
      return (
        !this.courseLoading && !this.assignmentLoading && this.course !== null
      )
    }
  },
  created() {
    const course_id = parseInt(this.$route.params.course_id)
    const assignment_id = parseInt(this.$route.params.assignment_id)

    this.$store.dispatch("course/setCurrent", course_id)
    this.$store.dispatch("assignment/setCurrent", { course_id, assignment_id })
  }
}
</script>

<style scoped></style>
