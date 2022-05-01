<template>
  <section>
    <empty-state
      v-if="courses.length === 0"
      icon="icon-time"
      title="You have no Courses"
      message="Your Courses will show up here when you sign up on Canvas"
    />

    <course-item
      v-for="course in currentCourses"
      :key="course.id"
      :course="course"
    />
    <pagination v-if="pages > 1" :pages="pages" @goto="gotoPage" />
  </section>
</template>

<script>
import CourseItem from "./CourseItem"
import Pagination from "../ui/Pagination"
import EmptyState from "../ui/EmptyState"

export default {
  components: {
    CourseItem,
    Pagination,
    EmptyState
  },
  props: {
    courses: {
      type: Array,
      required: true
    }
  },
  data: function() {
    return {
      page: 1
    }
  },
  computed: {
    pages: function() {
      return Math.ceil(this.courses.length / 10)
    },
    currentCourses: function() {
      const start = (this.page - 1) * 10
      const end = start + 9
      return this.courses.slice(start, end)
    }
  },
  methods: {
    gotoPage: function(page) {
      this.page = page
    }
  }
}
</script>

<style></style>
