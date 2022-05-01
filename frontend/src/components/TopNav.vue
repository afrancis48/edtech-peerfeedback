<template>
  <header>
    <nav class="navbar">
      <section class="navbar-section">
        <router-link :to="{ name: 'dashboard' }" class="navbar-brand mr-2">
          Peer Feedback
        </router-link>
      </section>
      <section class="navbar-section">
        <!-- Support Email -->
        <div v-if="isLoggedIn" class="dropdown dropdown-right">
          <a
            href="#"
            class="btn btn-default btn-link dropdown-toggle"
            tabindex="0"
          >
            <octicon name="heart" class="icon"></octicon> Help
          </a>
          <!-- Menu component -->
          <ul class="menu notification-list">
            <li class="menu-item">
              <div class="form-horizontal m-1">
                <p>
                  Get in touch using the form below or send us an
                  <a
                    href="mailto:gabriel@peerfeedback.io?Subject=Peer Feedback"
                  >
                    email
                  </a>
                </p>
                <div class="form-group" :class="{ 'has-error': emptySubject }">
                  <input
                    id="subject"
                    v-model="email.subject"
                    type="text"
                    class="form-input"
                    placeholder="Subject"
                    :disabled="sendingSupportMail"
                  />
                </div>
                <div class="form-group" :class="{ 'has-error': emptyMessage }">
                  <textarea
                    id="message"
                    v-model="email.message"
                    class="form-input"
                    name="message"
                    cols="15"
                    rows="5"
                    placeholder="How can we help you?"
                    :disabled="sendingSupportMail"
                  ></textarea>
                </div>
                <button
                  class="btn btn-primary"
                  :class="{ loading: sendingSupportMail }"
                  @click="sendEmail"
                >
                  Send
                </button>
              </div>
            </li>
          </ul>
        </div>

        <a
          v-else
          title="Peer Feedback Support"
          href="mailto:gabriel@peerfeedback.io?Subject=Peer Feedback"
          class="btn btn-link"
        >
          <octicon name="heart" class="icon"></octicon> Help
        </a>

        <a
          v-if="!isLoggedIn"
          id="login"
          href="#"
          class="btn btn-link"
          @click="login()"
        >
          <octicon class="icon" name="sign-in"></octicon> Login
        </a>

        <!-- Notifications -->
        <div
          v-if="isLoggedIn"
          class="dropdown dropdown-right"
          data-test="notificationsMenu"
        >
          <a
            href="#"
            class="btn btn-default btn-link dropdown-toggle"
            tabindex="1"
          >
            <octicon name="bell" class="icon" />
            <span
              v-if="groupedNotifications.length"
              class="badge"
              :data-badge="groupedNotifications.length"
            ></span>
          </a>
          <!-- menu component -->
          <ul class="menu notification-list" data-test="notificationDropdown">
            <li
              class="menu-header"
              :class="{ 'text-center': !groupedNotifications.length }"
            >
              <span v-if="!groupedNotifications.length">No</span> Notifications
              <span
                v-if="groupedNotifications.length"
                class="text-gray c-hand float-right"
                @click="clearAllNotifications"
              >
                Clear all notifications
              </span>
            </li>
            <li
              v-for="note in groupedNotifications"
              :key="note.id"
              class="menu-item notify-wrapper"
            >
              <notification :note="note"></notification>
            </li>
          </ul>
        </div>

        <!-- User Menu -->
        <div
          v-if="isLoggedIn"
          class="dropdown dropdown-right"
          data-test="userMenu"
        >
          <a
            href="#"
            class="btn btn-default btn-link dropdown-toggle"
            tabindex="0"
          >
            <avatar :user="currentUser" size="small" :link="false"></avatar>
          </a>
          <!-- menu component -->
          <ul class="menu small" data-test="userDropdown">
            <li class="menu-item">
              <div class="tile tile-centered">
                <div class="tile-icon">
                  <avatar :user="currentUser"></avatar>
                </div>
                <div class="tile-content">{{ currentUser.name }}</div>
              </div>
            </li>
            <li class="divider"></li>
            <li class="menu-item">
              <router-link
                :to="{ name: 'public-profile', params: { id: currentUser.id } }"
              >
                <octicon name="person"></octicon> Profile
              </router-link>
            </li>
            <li class="menu-item">
              <router-link :to="{ name: 'my-feedbacks' }">
                <octicon name="comment-discussion"></octicon> My Feedback
              </router-link>
            </li>
            <li class="menu-item">
              <router-link :to="{ name: 'user-settings' }">
                <octicon name="settings"></octicon> Settings
              </router-link>
            </li>
            <li class="divider"></li>
            <li class="menu-item">
              <router-link :to="{ name: 'logout' }">
                <octicon class="icon" name="sign-out"></octicon> Logout
              </router-link>
            </li>
          </ul>
        </div>
      </section>
    </nav>

    <bread-crumbs></bread-crumbs>
  </header>
</template>

<script>
import { mapGetters, mapActions, mapState } from "vuex"
import Octicon from "vue-octicon/components/Octicon"
import "vue-octicon/icons/bell"
import "vue-octicon/icons/person"
import "vue-octicon/icons/heart"
import "vue-octicon/icons/sign-in"
import "vue-octicon/icons/sign-out"
import "vue-octicon/icons/settings"
import "vue-octicon/icons/home"
import "vue-octicon/icons/check"
import Avatar from "./ui/Avatar"
import BreadCrumbs from "./ui/BreadCrumbs"
import Notification from "./ui/Notification"

export default {
  name: "TopNav",
  components: {
    Octicon,
    Avatar,
    BreadCrumbs,
    Notification
  },
  data: function() {
    return {
      email: {
        subject: "",
        message: ""
      },
      mailSent: false,
      emptySubject: false,
      emptyMessage: false
    }
  },
  computed: {
    ...mapGetters("user", ["isLoggedIn", "currentUser"]),
    ...mapGetters("notification", ["groupedNotifications"]),
    ...mapState("user", ["sendingSupportMail"])
  },
  watch: {
    $route: function() {
      if (this.isLoggedIn) this.$store.dispatch("notification/getNotifications")
    },
    isLoggedIn: function(logged) {
      if (logged) this.$store.dispatch("notification/getNotifications")
    },
    sendingSupportMail: function(now, then) {
      if (!now && then) {
        this.email.subject = this.email.message = ""
        this.emptySubject = this.emptyMessage = false
        this.mailSent = true
        this.showSentToast()
        setTimeout(() => (this.mailSent = false), 3000)
      }
    }
  },
  created() {
    this.$store.dispatch("notification/getNotifications")
  },
  methods: {
    ...mapActions("notification", ["clearAllNotifications"]),
    ...mapActions("user", ["sendSupportEmail"]),
    login: function() {
      window.location.href = "/users/login/"
    },
    sendEmail: function() {
      this.mailSent = false
      this.emptySubject = this.email.subject.trim().length === 0
      this.emptyMessage = this.email.message.trim().length === 0
      if (this.emptyMessage || this.emptySubject) return
      this.sendSupportEmail(this.email)
    },
    showSentToast: function() {
      this.$toasted.show("Thank you! (^-^)/ We will get back to you ASAP", {
        duration: 5000,
        type: "success"
      })
    }
  }
}
</script>

<style scoped>
.navbar {
  padding-top: 0.5em;
}
.dropdown .menu {
  box-shadow: 0 0.1rem 0.3rem 0 hsla(0, 0%, 0%, 0.5);
}
.dropdown .notification-list {
  width: 300px;
  max-height: 400px;
  padding: 0;
}
.menu-item.notify-wrapper {
  padding: 0;
}
.menu .menu-item + .menu-item {
  margin-top: 0;
}
.menu-header {
  font-size: small;
  height: 1.3rem;
  border-bottom: 1px solid #f0f1f4;
  padding: 0 0.3rem;
  position: sticky;
  position: -webkit-sticky;
  top: 0;
  background-color: #fff;
  z-index: 10;
}
</style>
