<template>
  <div>
    <div v-if="this.$route.name === 'course'">
      <!-- your homepage component -->
      <div class="columns page">
        <template v-if="!courseLoading && teacherOrTa">
          <div class="column col-12 text-center my-2 py-2">
            <h2>{{ course.name }}</h2>
            <p class="text-gray">
              {{ course.public_description | truncate(100, "...", true) }}
            </p>
            <router-link
              :to="{
                name: 'data-exporter',
                params: { course_id: course.id }
              }"
              class="btn btn-link btn-sm"
            >
              <octicon name="desktop-download" scale="1" class="icon" /> Get
              Course Data
            </router-link>
            <a :href="canvasLink">
              <octicon name="link-external" scale="1" class="icon" />
              <button class="btn btn-link btn-sm">View on Canvas</button>
            </a>
            <router-link
              :to="{
                name: 'course-wide-settings'
              }"
              class="btn btn-link btn-sm"
            >
              <octicon name="desktop-download" scale="1" class="icon" />
              Course-wide Settings
            </router-link>
          </div>
        </template>
        <div class="column col-6 col-sm-12">
          <h2>Assignments</h2>
          <content-placeholders v-if="assignmentsLoading">
            <content-placeholders-img />
            <content-placeholders-heading />
            <content-placeholders-text :lines="2" />
          </content-placeholders>

          <empty-state
            v-if="!assignmentsLoading && !assignments.length"
            icon="icon-flag"
            title="No Assignments"
            message="There are no assignments for this course in the Peer Feedback system."
          ></empty-state>

          <div v-if="assignments.length && course !== null">
            <assignment-card
              v-for="assignment in assignments"
              :key="assignment.id"
              :assignment="assignment"
              :course-id="course.id"
              :teacher-or-ta="teacherOrTa"
            />
          </div>

          <h2 class="h2 mt-2 pt-2">Within-group Anonymous Reviews</h2>
          <empty-state
            v-if="!assignmentsLoading && !igrs.length"
            icon="icon-flag"
            title="No Within-group Anonymous Reviews"
            message="There are no within-group anonymous reviews for this course in the Peer Feedback system."
          />

          <div v-if="igrs.length && course !== null">
            <assignment-card
              v-for="igr in igrs"
              :key="igr.id"
              :assignment="igr"
              :course-id="course.id"
              :teacher-or-ta="teacherOrTa"
            />
          </div>
        </div>

        <div class="column col-6 col-sm-12">
          <h2>Course Tasks</h2>

          <content-placeholders
            v-if="tasksLoading && incompleteTasks.length === 0"
          >
            <content-placeholders-heading />
            <content-placeholders-text :lines="2" />
            <content-placeholders-heading />
            <content-placeholders-text :lines="2" />
          </content-placeholders>

          <empty-state
            v-if="!tasksLoading && incompleteTasks.length === 0"
            icon="icon-time"
            title="You have no Tasks"
            message="Your tasks will show up here when you are assigned a peer for feedback"
          >
          </empty-state>

          <div class="mt-2">
            <tasks :incomplete-tasks="incompleteTasks"></tasks>
          </div>
        </div>
      </div>
    </div>
    <router-view></router-view>
  </div>
</template>

<script>
import { mapState, mapGetters } from "vuex"

import AssignmentCard from "@/components/assignment/AssignmentCard"
import EmptyState from "../components/ui/EmptyState"
import Tasks from "../components/ui/Tasks"
import Octicon from "vue-octicon/components/Octicon"
import "vue-octicon/icons/desktop-download"
import "vue-octicon/icons/link-external"

import CourseAPI from "../api/course.js"

export default {
  components: {
    AssignmentCard,
    Octicon,
    EmptyState,
    Tasks
  },
  computed: {
    ...mapState({
      courseLoading: state => state.course.isLoading,
      course: state => state.course.current,
      assignmentsLoading: state => state.assignment.isLoading,
      tasks: state => state.tasks.tasks,
      tasksLoading: state => state.task.isLoading
    }),
    ...mapGetters({
      assignments: "assignment/regular",
      igrs: "assignment/igrs"
    }),
    ...mapGetters("task", ["incompleteTasks"]),
    ...mapGetters("course", ["role"]),
    teacherOrTa: function() {
      return this.role === "teacher" || this.role === "ta"
    },
    canvasLink: function() {
      const course_id = parseInt(this.$route.params.id)

      return `https://gatech.instructure.com/courses/${course_id}`
    }
  },
  created() {
    const course_id = parseInt(this.$route.params.id)
    this.$store.dispatch("course/setCurrent", course_id)
    this.$store.dispatch("assignment/getAssignmentsInCourse", course_id)
    this.$store.dispatch("task/getCourseTasks", course_id)
  },
  methods: {
    download: function() {
      const course_id = parseInt(this.$route.params.id)
      CourseAPI.getData(
        course_id,
        response => {
          console.log(response)
          this.$toasted.show("You will receive a download link via email!", {
            duration: 3000,
            type: "info"
          })
        },
        err => {
          console.log(err)
          this.$toasted.show("There was an error creating your download.", {
            duration: 3000,
            type: "error"
          })
        }
      )
    }
  }
}
</script>

<style scoped>
.card {
  margin-top: 0.2rem;
}
.card-title .icon {
  margin-top: -0.2rem;
}

.course-tile {
  margin-top: 0.8rem;
  margin-bottom: 2.5rem;
}
</style>
