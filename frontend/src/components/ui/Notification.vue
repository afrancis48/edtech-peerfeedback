<template>
  <div class="notification tile tile-centered" @click="goToPage(note)">
    <div class="tile-icon">
      <octicon
        v-if="note.item === 'medal'"
        name="mortar-board"
        class="icon"
        scale="2"
      ></octicon>
      <octicon
        v-if="note.item === 'feedback'"
        name="megaphone"
        class="icon"
        scale="2"
      ></octicon>
      <octicon
        v-if="note.item === 'comment'"
        name="comment-discussion"
        class="icon"
        scale="2"
      ></octicon>
      <octicon
        v-if="note.item === 'like'"
        name="thumbsup"
        class="icon"
        scale="2"
      ></octicon>
    </div>
    <div class="tile-content">
      <div v-if="note.item === 'medal'" class="tile-title">
        You have been awarded <strong>a new medal</strong>.
      </div>
      <div v-else-if="!note.notifier" class="tile-title">
        A team member gave you feedback for {{ note.assignment_name }}
      </div>
      <div v-else class="tile-title">
        {{ note.notifier.name }}
        <span v-if="note.item === 'comment'">commented on</span>
        <span v-if="note.item === 'feedback'">gave feedback on</span>
        <span v-if="note.item === 'like'">liked your comment on</span>

        <span v-if="note.user_id === currentUser.id"> your </span>
        <span v-else> {{ note.user.name }}'s</span>

        <span>
          submission for <em>{{ note.assignment_name }}</em
          >.
        </span>
      </div>
      <div v-if="note.item === 'medal'" class="tile-subtitle text-gray">
        Congratulations
      </div>
      <div v-else class="tile-subtitle text-gray">
        <octicon name="repo" class="icon"></octicon> {{ note.course_name }}
      </div>
      <div class="tile-subtitle float-right">
        <octicon name="history" class="icon"></octicon>
        {{ notifiedDuration }} ago
      </div>
    </div>
  </div>
</template>

<script>
import Octicon from "vue-octicon/components/Octicon"
import "vue-octicon/icons/mortar-board"
import "vue-octicon/icons/history"
import "vue-octicon/icons/repo"
import "vue-octicon/icons/megaphone"
import "vue-octicon/icons/thumbsup"
import "vue-octicon/icons/comment-discussion"
import { mapGetters } from "vuex"

export default {
  name: "Notification",
  components: {
    Octicon
  },
  filters: {
    firstName: function(value) {
      if (typeof value !== "string") return
      return value.split(" ", 2)[0]
    }
  },
  props: {
    note: {
      type: Object,
      required: true
    }
  },
  computed: {
    ...mapGetters("user", ["currentUser"]),
    notifiedDuration: function() {
      let delta = (new Date() - new Date(this.note.created_on)) / 1000
      if (delta < 60) {
        return "a few seconds"
      } else if (delta < 3600) {
        delta = Math.floor(delta / 60)
        return delta + " minute" + (delta > 1 ? "s" : "")
      } else if (delta < 86400) {
        delta = Math.floor(delta / 3600)
        return delta + " hour" + (delta > 1 ? "s" : "")
      } else if (delta < 604800) {
        delta = Math.floor(delta / 86400)
        return delta + " day" + (delta > 1 ? "s" : "")
      } else {
        delta = Math.floor(delta / 604800)
        return delta + " week" + (delta > 1 ? "s" : "")
      }
    }
  },
  methods: {
    goToSubmission: function(notification) {
      this.$router.push({
        name: "give-feedback",
        params: notification,
        hash: `#${notification.item}_${notification.item_id}`
      })
    },
    goToProfile: function() {
      this.$router.push({
        name: "public-profile",
        params: { id: this.currentUser.id }
      })
    },
    goToPage: function(notification) {
      this.$store.dispatch("notification/markNotificationRead", notification.id)
      if (notification.item === "medal") this.goToProfile()
      else this.goToSubmission(notification)
    }
  }
}
</script>

<style scoped>
.notification {
  font-size: 12px;
  height: auto;
  width: auto;
  padding: 0.2rem 0.2rem;
  border-bottom: 1px solid #f0f1f4;
  cursor: pointer;
}
.tile.tile-centered .tile-title,
.tile.tile-centered .tile-subtitle {
  overflow-x: auto;
  white-space: normal;
  line-height: 0.9rem;
  padding-bottom: 0.2rem;
}

.notification:hover {
  background-color: #f1f1fc;
}
</style>
