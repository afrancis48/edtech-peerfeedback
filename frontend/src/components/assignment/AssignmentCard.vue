<template>
  <div class="card" data-test="assignmentCard">
    <div class="card-header">
      <div class="card-title h6">
        <octicon name="book" class="icon" /> {{ assignment.name }}
      </div>
      <div v-if="assignment.due_at" class="card-subtitle text-gray">
        <small>
          <span class="text-dark text-bold">
            <octicon class="icon" name="clock"></octicon>
            {{ assignment.intra_group_review ? "Due at" : "Assignment due" }}
          </span>
          <span class="text-dark ml-1">{{
            assignment.due_at | readableDate
          }}</span>
        </small>
      </div>
    </div>
    <div class="card-body" v-html="assignment.description"></div>
    <div class="card-footer">
      <router-link
        v-if="teacherOrTa"
        :to="{
          name: 'assignment.settings',
          params: { course_id: courseId, assignment_id: assignment.id }
        }"
        class="btn btn-primary"
      >
        View
      </router-link>
      <router-link
        v-else
        :to="{
          name: 'assignment',
          params: { course_id: courseId, assignment_id: assignment.id }
        }"
        class="btn btn-primary"
      >
        View
      </router-link>
    </div>
  </div>
</template>

<script>
import Octicon from "vue-octicon/components/Octicon"
import "vue-octicon/icons/book"
import "vue-octicon/icons/clock"

export default {
  name: "AssignmentCard",
  components: {
    Octicon
  },
  props: {
    courseId: {
      type: Number,
      required: true
    },
    assignment: {
      type: Object,
      required: true
    },
    teacherOrTa: {
      type: Boolean,
      required: true
    }
  }
}
</script>

<style scoped></style>
