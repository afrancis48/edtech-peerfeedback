<template>
  <div class="container grid-lg">
    <div class="columns">
      <div class="column col-2 col-xs-12">
        <ul class="menu">
          <li class="menu-item" @click="currentPage = 'profile'">
            <a href="#profile" :class="{ active: currentPage === 'profile' }">
              Profile
            </a>
          </li>
          <li class="menu-item" @click="currentPage = 'preferences'">
            <a
              href="#preferences"
              :class="{ active: currentPage === 'preferences' }"
            >
              Preferences
            </a>
          </li>
          <li class="menu-item">
            <router-link :to="{ name: 'logout' }">Logout</router-link>
          </li>
        </ul>
      </div>
      <div class="column col-9 col-xs-12 col-ml-auto">
        <user-profile-settings
          v-if="currentPage === 'profile'"
        ></user-profile-settings>
        <user-preferences
          v-if="currentPage === 'preferences'"
        ></user-preferences>
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters } from "vuex"
import UserProfileSettings from "../components/user/UserProfileSettings"
import UserPreferences from "../components/user/UserPreferences"

export default {
  name: "UserSettings",
  components: {
    UserProfileSettings,
    UserPreferences
  },
  data: function() {
    return {
      currentPage: "profile"
    }
  },
  computed: {
    ...mapGetters("user", ["currentUser"])
  },
  created() {
    // Use the # marker in the url to load appropriate page
    let page = this.$route.hash.slice(1)
    switch (page) {
      case "profile":
      case "preferences":
        this.currentPage = page
        break
    }
  }
}
</script>

<style scoped></style>
