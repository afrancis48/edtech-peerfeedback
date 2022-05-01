<template>
  <div class="card my-2">
    <div v-if="course.image_download_url" class="card-image">
      <img
        class="img-responsive"
        :src="course.image_download_url"
        alt="Course image"
      />
    </div>
    <div class="card-header">
      <div class="card-title h5">{{ course.name }}</div>
      <div class="card-subtitle text-gray">{{ course.term.name }}</div>
    </div>
    <div class="card-body">
      <template v-if="course.public_description">
        {{ course.public_description | truncate(250, "...", true) }}
      </template>
    </div>
    <div class="card-footer">
      <router-link
        :to="{ name: 'course', params: { id: course.id } }"
        class="btn btn-primary"
      >
        View
      </router-link>
    </div>
  </div>
</template>

<script>
export default {
  name: "CourseItem",
  props: {
    course: {
      type: Object,
      required: true
    }
  }
}
</script>

<style scoped></style>
