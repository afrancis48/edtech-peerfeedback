<template>
  <div class="empty">
    <div class="empty-icon"><octicon name="telescope" scale="4"></octicon></div>
    <p class="empty-title h3">404 Not Found</p>
    <p class="empty-subtitle">
      The world is yours to explore. Never stop exploring.
    </p>
    <div class="empty-action">
      <router-link to="/dashboard/" class="btn btn-primary">
        Go home for now
      </router-link>
    </div>
  </div>
</template>

<script>
import Octicon from "vue-octicon/components/Octicon"
import "vue-octicon/icons/telescope"

export default {
  name: "NotFound404",
  components: {
    Octicon
  }
}
</script>

<style scoped></style>
