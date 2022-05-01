<template>
  <section v-if="isLoggedIn && dataLoaded" id="breadcrumbs">
    <ul class="breadcrumb">
      <li class="breadcrumb-item">
        <octicon class="icon" name="home"></octicon>
        <router-link :to="{ name: 'dashboard' }"> Home</router-link>
      </li>
      <li v-for="crumb in crumbs" :key="crumb.text" class="breadcrumb-item">
        <router-link :to="crumb.link">{{ crumb.text }}</router-link>
      </li>
    </ul>
  </section>
</template>

<script>
import Octicon from "vue-octicon/components/Octicon"
import { mapGetters, mapState } from "vuex"

export default {
  name: "BreadCrumbs",
  components: {
    Octicon
  },
  computed: {
    ...mapGetters("user", ["isLoggedIn", "currentUser"]),
    ...mapGetters("course", ["role"]),
    ...mapState({
      course: state => state.course.current,
      courseLoading: state => state.course.isLoading,
      assignment: state => state.assignment.current,
      assignmentLoading: state => state.assignment.isLoading,
      submission: state => state.submission.current,
      submissionLoading: state => state.submission.isLoading
    }),
    dataLoaded: function() {
      let name = this.$route.name
        ? this.$route.name.split(".")[0]
        : "give-feedback"
      switch (name) {
        case "course":
        case "data-exporter":
          return !this.courseLoading
        case "assignment":
          return !(this.courseLoading || this.assignmentLoading)
        case "give-feedback":
          return !(
            this.courseLoading ||
            this.assignmentLoading ||
            this.submissionLoading
          )
        default:
          return true
      }
    },
    feedbackPageCrumbText: function() {
      if (!this.submission) return "Submission"

      if (this.currentUser.id === this.$route.params.user_id) {
        return "Your Submission"
      } else {
        return `${this.submission.user.name}'s submission`
      }
    },
    crumbs: function() {
      let { name, params, meta } = this.$route
      name = name.split(".")[0]

      if (name === "dashboard") {
        return []
      }

      let assignment_route = "assignment"
      if (this.role !== "student") assignment_route = "assignment.settings"
      let course_text = this.course
        ? `${this.course.name} (${this.course.term.name})`
        : ""

      switch (name) {
        case "course":
          return [{ link: { name, params }, text: course_text }]
        case "assignment":
          return [
            {
              link: { name: "course", params: { id: params.course_id } },
              text: course_text
            },
            {
              link: { name: assignment_route, params },
              text: this.assignment.name
            }
          ]
        case "give-feedback":
          return [
            {
              link: { name: "course", params: { id: params.course_id } },
              text: course_text
            },
            {
              link: { name: assignment_route, params },
              text: this.assignment.name
            },
            { link: { name, params }, text: this.feedbackPageCrumbText }
          ]
        case "data-exporter":
          return [
            {
              link: { name: "course", params: { id: params.id } },
              text: course_text
            },
            {
              link: { name, params },
              text: meta.desc
            }
          ]
        case "course-wide-settings":
          return [
            {
              link: { name: "course", params: { id: params.id } },
              text: course_text
            },
            {
              link: { name, params },
              text: meta.desc
            }
          ]
        default:
          return [{ link: { name, params }, text: meta.desc }]
      }
    }
  }
}
</script>

<style scoped>
.breadcrumb-item {
  font-size: small;
}
.breadcrumb-item > .icon {
  margin-top: -5px;
}
.breadcrumb {
  margin-bottom: 1rem;
}
</style>
