<template>
  <div class="columns page">
    <div class="column col-6 col-sm-12">
      <h2>Active Courses</h2>

      <content-placeholders v-if="coursesLoading && activeCourses.length === 0">
        <content-placeholders-heading />
        <content-placeholders-text :lines="2" />
        <content-placeholders-heading />
        <content-placeholders-text :lines="2" />
      </content-placeholders>

      <div v-else class="mt-2">
        <courses :courses="activeCourses"></courses>
      </div>
      <div class="mt-2 text-right">
        <router-link :to="{ name: 'all-courses' }">All courses</router-link>
      </div>
    </div>
    <div class="column col-6 col-sm-12 col-mx-auto">
      <h2>Pending Tasks</h2>
      <content-placeholders v-if="tasksLoading && incompleteTasks.length === 0">
        <content-placeholders-heading />
        <content-placeholders-text :lines="2" />
        <content-placeholders-heading />
        <content-placeholders-text :lines="2" />
      </content-placeholders>

      <empty-state
        v-if="!tasksLoading && incompleteTasks.length === 0"
        icon="icon-time"
        title="All done for now!"
        message="For extra feedback tasks go to Course -> Assignment -> View"
      >
      </empty-state>

      <div class="mt-2">
        <tasks :incomplete-tasks="incompleteTasks"></tasks>
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters, mapState } from "vuex"
import { initials } from "../utils"

import EmptyState from "../components/ui/EmptyState"
import Tasks from "../components/ui/Tasks"
import Courses from "../components/course/Courses"

export default {
  components: {
    EmptyState,
    Tasks,
    Courses
  },
  computed: {
    ...mapGetters("task", ["incompleteTasks"]),
    ...mapGetters("course", ["activeCourses"]),
    ...mapState({
      coursesLoading: state => state.course.isLoading,
      tasks: state => state.task.tasks,
      tasksLoading: state => state.task.isLoading
    })
  },
  created() {
    this.$store.dispatch("course/getCourses")
    this.$store.dispatch("task/getIncompleteTasks")
  },
  methods: {
    initials
  }
}
</script>

<style></style>
