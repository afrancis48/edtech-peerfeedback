<template>
  <div
    id="modal-id"
    class="modal"
    :class="{
      active: showModal,
      'modal-sm': size === 'small',
      'modal-lg': size === 'large'
    }"
  >
    <div class="modal-overlay"></div>
    <div class="modal-container">
      <div class="modal-header">
        <div class="modal-title h5">{{ title }}</div>
      </div>
      <div class="modal-body">
        <div class="content"><slot></slot></div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-primary" @click="$emit('confirmed')">
          {{ confirm }}
        </button>
        <button class="btn btn-default ml-2" @click="$emit('rejected')">
          {{ reject }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "ConfirmModal",
  props: {
    title: {
      type: String,
      required: true
    },
    showModal: {
      type: Boolean,
      required: true
    },
    confirm: {
      type: String,
      required: true
    },
    reject: {
      type: String,
      required: true
    },
    size: {
      type: String,
      default: "medium"
    }
  }
}
</script>

<style scoped>
.modal.modal-lg .modal-overlay {
  background-color: #fff;
  opacity: 0.9;
}
.modal .modal-container {
  padding: 0;
  box-shadow: 0 2px 6px 0 hsla(0, 0%, 0%, 0.3);
}
.modal .modal-footer,
.modal-header {
  background-color: #f8f9fa;
}
</style>
