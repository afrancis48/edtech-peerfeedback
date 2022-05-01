<template>
  <div id="modal-id" class="modal" :class="modalClass">
    <a href="#close" class="modal-overlay" aria-label="Close"></a>
    <div class="modal-container">
      <div class="modal-header">
        <a
          href="#close"
          class="btn btn-clear float-right"
          aria-label="Close"
          @click="close"
        ></a>
        <div class="modal-title h5">{{ title }}</div>
      </div>
      <div class="modal-body">
        <div class="content"><slot></slot></div>
      </div>
      <div class="modal-footer"></div>
    </div>
  </div>
</template>

<script>
export default {
  name: "Modal",
  props: {
    title: {
      type: String,
      default: ""
    },
    showModal: {
      type: Boolean,
      required: true
    },
    size: {
      type: String,
      required: false,
      default: ""
    }
  },
  computed: {
    modalClass: function() {
      return {
        active: this.showModal,
        "modal-lg": this.size === "lg" || this.size === "large",
        "modal-sm": this.size === "sm" || this.size === "small"
      }
    }
  },
  mounted: function() {
    document.addEventListener("keydown", e => {
      if (e.code === "Escape") this.close()
    })
  },
  methods: {
    close: function() {
      const vm = this
      vm.$emit("modalClosed")
    }
  }
}
</script>
