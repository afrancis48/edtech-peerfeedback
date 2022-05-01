<template>
  <div>
    <content-placeholders v-if="profileLoading">
      <content-placeholders-heading />
      <content-placeholders-text :lines="2" />
      <content-placeholders-heading />
      <content-placeholders-text :lines="2" />
    </content-placeholders>

    <form v-if="!profileLoading" class="form-horizontal">
      <div class="form-group">
        <div class="col-3 col-sm-12">
          <label class="form-label" for="username">Username</label>
        </div>
        <div class="col-9 col-sm-12">
          <input
            id="username"
            class="form-input"
            type="text"
            :value="profile.username"
            autocomplete="username"
            disabled
          />
        </div>
      </div>

      <div class="form-group">
        <div class="col-3 col-sm-12">
          <label class="form-label" for="display_name">Full Name</label>
        </div>
        <div class="col-9 col-sm-12">
          <input
            id="display_name"
            v-model="profile.name"
            class="form-input"
            type="text"
            autocomplete="name"
          />
        </div>
      </div>

      <div class="form-group">
        <div class="col-3 col-sm-12">
          <label class="form-label" for="email">Email</label>
        </div>
        <div class="col-9 col-sm-12">
          <input
            id="email"
            v-model="profile.email"
            class="form-input"
            type="text"
            autocomplete="email"
          />
        </div>
      </div>

      <div class="form-group">
        <div class="col-3 col-sm-12">
          <label for="bio" class="form-label">Short Bio</label>
        </div>
        <div class="col-9 col-sm-12">
          <textarea
            id="bio"
            v-model="profile.bio"
            class="form-input"
            placeholder="Your bio"
            rows="3"
          ></textarea>
        </div>
      </div>

      <a
        class="btn btn-primary float-right"
        :class="{ loading: updating }"
        @click="updateProfile()"
      >
        Update Profile
      </a>
    </form>
  </div>
</template>

<script>
import { mapActions, mapState } from "vuex"

export default {
  name: "UserProfile",
  computed: {
    ...mapState("user", ["profileLoading", "updating"]),
    profile: {
      get() {
        return this.$store.state.user.profile
      },
      set(value) {
        this.$store.commit("user/setProfile", value)
      }
    }
  },
  created() {
    this.$store.dispatch("user/getProfile")
  },
  methods: {
    ...mapActions("user", ["updateProfile"])
  }
}
</script>

<style scoped></style>
