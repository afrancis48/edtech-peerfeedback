<template>
  <div class="form-autocomplete">
    <!-- autocomplete input container -->
    <div class="form-autocomplete-input form-input">
      <!-- autocomplete tiles -->
      <div v-if="chosenUser" class="tile tile-centered">
        <div class="tile-icon">
          <avatar :user="chosenUser" size="small"></avatar>
        </div>
        <div class="tile-content">{{ chosenUser.name }}</div>
      </div>

      <!-- autocomplete real input box -->
      <input
        v-model="inputText"
        title="User name or Email"
        class="form-input"
        type="text"
        :placeholder="placeholder"
        @keyup.delete="resetUser()"
        @blur="clearSuggestions()"
      />
    </div>

    <!-- autocomplete suggestion list -->
    <ul v-show="suggestions.length" class="menu">
      <!-- menu list items -->
      <li v-for="user in suggestions" :key="user.email" class="menu-item">
        <a href="#" @mousedown="selectUser(user)">
          {{ user | nameAndEmail }}
        </a>
      </li>
    </ul>
  </div>
</template>

<script>
import fuzzaldrin from "fuzzaldrin"
import Avatar from "./Avatar"

export default {
  name: "UserSelector",
  components: {
    Avatar
  },
  props: {
    users: {
      type: Array,
      required: true
    },
    placeholder: {
      type: String,
      required: false,
      default: "Name or Email"
    }
  },
  data: function() {
    return {
      chosenUser: null,
      stopSuggesting: false,
      suggestions: [],
      inputText: ""
    }
  },
  watch: {
    inputText: function(text) {
      const self = this
      self.suggestions = []

      let emails = fuzzaldrin.filter(self.users, text, { key: "email" })
      let names = fuzzaldrin.filter(self.users, text, { key: "name" })
      self.suggestions = Array.from(new Set([...emails, ...names]))
    }
  },
  methods: {
    clearSuggestions: function() {
      const self = this
      setTimeout(() => {
        self.suggestions = []
      }, 50)
    },
    resetUser: function() {
      const self = this
      self.chosenUser = null
      self.$emit("input", null)
    },
    selectUser: function(user) {
      this.inputText = " "
      this.chosenUser = user
      this.$emit("input", user)
    }
  }
}
</script>

<style scoped></style>
