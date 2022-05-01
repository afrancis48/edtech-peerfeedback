<template>
  <div class="empty">
    <div class="empty-icon"><i class="icon icon-2x" :class="icon"></i></div>
    <p class="empty-title h5">{{ title }}</p>
    <p v-if="message" class="empty-subtitle">{{ message }}</p>
    <div class="empty-action">
      <button
        v-if="action"
        class="btn btn-default"
        @click="$emit('empty-action')"
      >
        {{ action }}
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: "EmptyState",
  props: {
    icon: {
      type: String,
      required: false,
      default: "icon-flag"
    },
    title: {
      type: String,
      required: true
    },
    message: {
      type: String,
      default: ""
    },
    action: {
      type: String,
      default: null
    }
  }
}
</script>

<style scoped></style>
