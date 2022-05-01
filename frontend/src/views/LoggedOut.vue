<template>
  <div class="empty">
    <div class="empty-icon"><i class="icon icon-check"></i></div>
    <p class="empty-title h5">You have logged out.</p>
  </div>
</template>

<script>
import { mapActions } from "vuex"
import { deleteAllCookies } from "../utils"

export default {
  name: "LoggedOut",
  created() {
    this.logout()
    deleteAllCookies()
  },
  methods: {
    ...mapActions("user", ["logout"])
  }
}
</script>

<style></style>
