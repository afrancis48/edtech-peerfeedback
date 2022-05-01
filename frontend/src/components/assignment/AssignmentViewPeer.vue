<template>
  <div class="columns">
    <div v-if="peersLoading" class="column col-12">
      <content-placeholders>
        <content-placeholders-text :lines="1" />
        <content-placeholders-heading />
      </content-placeholders>
    </div>

    <div v-if="!peersLoading" class="column col-12">
      <!-- Autocomplete -->
      <div class="form-autocomplete">
        <div class="input-group">
          <!-- autocomplete input container -->
          <div class="form-autocomplete-input form-input">
            <div v-if="peerSelected" class="tile tile-centered">
              <div class="tile-icon">
                <avatar :user="chosenPeer" size="small"></avatar>
              </div>
              <div class="tile-content">{{ chosenPeer.name }}</div>
            </div>
            <!-- autocomplete real input box -->
            <input
              id="input-example-2"
              v-model="peerEmail"
              title="Peer name or Email"
              class="form-input"
              :placeholder="placeholder"
              type="email"
              style="width: inherit;"
              @keyup.delete="resetPeer()"
              @blur="clearSuggestion()"
            />
          </div>
          <button class="btn input-group-btn" @click="selectPeer()">
            Pick a peer for me
          </button>
        </div>

        <!-- autocomplete suggestion list -->
        <ul v-show="suggestions.length" class="menu">
          <!-- menu list chips -->
          <li
            v-for="suggestion in suggestions"
            :key="suggestion.id"
            class="menu-item"
          >
            <a href="#" @click="selectPeer(suggestion)">
              {{ suggestion | nameAndEmail }}
            </a>
          </li>
        </ul>
      </div>
      <!-- ./Autocomplete -->
    </div>

    <div v-if="!peersLoading" class="column col-12 my-2">
      <div class="form-group">
        <button
          class="btn btn-primary"
          :disabled="!peerSelected"
          @click="viewAssignment()"
        >
          View Feedback
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import Vue from "vue"
import fuzzaldrin from "fuzzaldrin"
import { mapActions, mapState } from "vuex"
import Avatar from "../ui/Avatar"

Array.prototype.shuffle = function() {
  let i = this.length,
    j,
    temp
  if (i === 0) return this
  while (--i) {
    j = Math.floor(Math.random() * (i + 1))
    temp = this[i]
    this[i] = this[j]
    this[j] = temp
  }
  return this
}

Vue.filter("nameAndEmail", function(user) {
  if (user.hasOwnProperty("primary_email")) {
    return user.name + " ( " + user.primary_email + " )"
  } else if (user.hasOwnProperty("email")) {
    return user.name + " (" + user.email + ")"
  }
  return user.name
})

export default {
  name: "AssignmentViewPeer",
  components: {
    Avatar
  },
  props: {
    assignment: {
      type: Object,
      required: true
    }
  },
  data: function() {
    return {
      peerSelected: false,
      chosenPeer: null,
      stopSuggesting: false,
      suggestions: [],
      peerEmail: "",
      placeholder: "Student name or email"
    }
  },
  computed: {
    ...mapState({
      peers: state => state.assignment.peers,
      peersLoading: state => state.assignment.peersLoading
    }),
    peerLink: function() {
      if (this.chosenPeer === null || !this.chosenPeer.hasOwnProperty("id"))
        return "#"

      const params = {
        course_id: this.$route.params.course_id,
        user_id: this.chosenPeer.id,
        assignment_id: this.$route.params.assignment_id,
        view_only: "true"
      }
      return { name: "give-feedback", params }
    }
  },
  watch: {
    peerEmail: function(newEmail) {
      const self = this
      self.suggestions = []

      if (self.stopSuggesting) {
        self.stopSuggesting = !self.stopSuggesting
        return
      }

      let emails = fuzzaldrin.filter(self.peers, newEmail, { key: "email" })
      let names = fuzzaldrin.filter(self.peers, newEmail, { key: "name" })
      this.suggestions = Array.from(new Set([...emails, ...names]))
    }
  },
  created() {
    this.$store.dispatch("assignment/getPeers", this.$route.params)
  },
  methods: {
    ...mapActions("pairing", ["pairUser"]),
    resetPeer: function() {
      this.chosenPeer = null
      this.peerSelected = false
      this.stopSuggesting = false
    },
    clearSuggestion: function() {
      const self = this
      setTimeout(() => {
        self.suggestions = []
      }, 500)
    },
    selectPeer: function(peer) {
      if (typeof peer === "undefined") {
        // choose the peer with the least number of feedback
        let filtered = this.peers.filter(peer => peer.extra_requested)
        if (!filtered.length) filtered = this.peers
        this.chosenPeer = filtered
          .shuffle()
          .reduce((p, c) => (p.feedbacks < c.feedbacks ? p : c))
      } else {
        this.chosenPeer = peer
      }

      this.peerEmail = " "
      this.stopSuggesting = true
      this.suggestions = []
      this.peerSelected = true
      this.placeholder = ""
    },
    viewAssignment: function() {
      const self = this
      let data = {
        course_id: self.$route.params.course_id,
        course_name: self.assignment.course_name,
        assignment_id: self.$route.params.assignment_id,
        assignment_name: self.assignment.name,
        recipient_id: self.chosenPeer.id,
        recipient_name: self.chosenPeer.name,
        view_only: true
      }
      self
          .pairUser(data)
          .then(() => self.$router.push(self.peerLink))
          .catch(error => {
          // If Pairing has already been done, then just load the give feedback page
          if (error.response.status === 409) {
            self.$router.push(self.peerLink)
            return
          }

          let errorMsg = ""
          if (error.response.data && error.response.data.message) {
            errorMsg = error.response.data.message
          } else {
            errorMsg = `Failed to view assignment. ${error.response.status} ${
              error.response.statusText
            }.`
          }
          self.$toasted.error(errorMsg, { duration: 5000 })
        })
    }
  }
}
</script>

<style scoped></style>
