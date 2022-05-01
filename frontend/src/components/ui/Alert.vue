<template>
  <div class="alert" :class="alertClass">
    <octicon :name="icon" class="icon"></octicon> {{ msg }}
  </div>
</template>

<script>
import Octicon from "vue-octicon/components/Octicon"
import "vue-octicon/icons/info"
import "vue-octicon/icons/alert"
import "vue-octicon/icons/stop"
import "vue-octicon/icons/megaphone"
import "vue-octicon/icons/verified"

export default {
  name: "Alert",
  components: {
    Octicon
  },
  props: {
    state: {
      type: String,
      required: false,
      default: ""
    },
    msg: {
      type: String,
      required: true
    }
  },
  computed: {
    alertClass: function() {
      switch (this.state) {
        case "info":
          return "alert-info"
        case "warning":
          return "alert-warning"
        case "error":
          return "alert-error"
        case "success":
          return "alert-success"
        default:
          return "alert-default"
      }
    },
    icon: function() {
      switch (this.state) {
        case "info":
          return "info"
        case "warning":
          return "alert"
        case "error":
          return "stop"
        case "success":
          return "verified"
        default:
          return "megaphone"
      }
    }
  }
}
</script>

<style scoped>
.alert {
  border-radius: 0.2rem;
  border: 1px solid #f0f1f4;
  padding: 1rem;
  background-color: #f8f9fa;
  text-align: left;
  border-top: 3px solid #acb3c2;
}
.alert > .icon {
  margin-top: -0.2rem;
  margin-right: 0.25rem;
}
.alert.alert-info {
  background-color: #f1f1fc;
  border-top-color: #5755d9;
  color: #5755d9;
}
.alert.alert-warning {
  background-color: #fff6cc;
  border-top-color: #b37700;
  color: #b37700;
}
.alert.alert-error {
  background-color: #ffeae6;
  border-top-color: #cc0000;
  color: #cc0000;
}
.alert.alert-success {
  background-color: #e6ffe6;
  border-top-color: #008800;
  color: #008800;
}
</style>
