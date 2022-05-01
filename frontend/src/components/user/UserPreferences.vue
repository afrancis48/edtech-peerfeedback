<template>
  <div>
    <content-placeholders v-if="settingsLoading">
      <content-placeholders-heading />
      <content-placeholders-text :lines="2" />
      <content-placeholders-heading />
      <content-placeholders-text :lines="2" />
    </content-placeholders>

    <form v-if="!settingsLoading" class="form-horizontal">
      <div class="form-group">
        <div class="col-3 col-sm-12">
          <label class="form-label"><strong>Email Preferences</strong></label>
        </div>
        <div class="col-9 col-sm-12">
          <p>Send me emails when someone</p>
          <div class="form-group">
            <label class="form-switch">
              <input
                v-model="settings.feedback_emails"
                type="checkbox"
                @change="updateSettings()"
              />
              <i class="form-icon"></i> gives <em>feedback</em> on my assignment
            </label>
          </div>

          <div class="form-group">
            <label class="form-switch">
              <input
                v-model="settings.comment_emails"
                type="checkbox"
                @change="updateSettings()"
              />
              <i class="form-icon"></i> <em>comments</em> on my assignment
            </label>
          </div>

          <div class="form-group">
            <label class="form-switch">
              <input
                v-model="settings.discussion_emails"
                type="checkbox"
                @change="updateSettings()"
              />
              <i class="form-icon"></i> comments on
              <em>assignments I review</em>
            </label>
          </div>

          <div class="py-2"><div class="divider"></div></div>
          <p>When I am a TA or Teacher of a course</p>

          <div class="form-group">
            <label class="form-switch">
              <input
                v-model="settings.pairing_emails"
                type="checkbox"
                @change="updateSettings()"
              />
              <i class="form-icon"></i> Notify once auto pairing is complete
            </label>
          </div>
        </div>
      </div>
    </form>
  </div>
</template>

<script>
import { mapActions, mapState } from "vuex"

export default {
  name: "UserPreferences",
  computed: {
    ...mapState("user", ["settingsLoading", "updating"]),
    settings: {
      get() {
        return this.$store.state.user.settings
      },
      set(value) {
        this.$store.commit("user/setSettings", value)
      }
    }
  },
  created() {
    this.$store.dispatch("user/getSettings")
  },
  methods: {
    ...mapActions("user", ["updateSettings"])
  }
}
</script>

<style scoped></style>
