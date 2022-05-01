<template>
  <div class="form-autocomplete">
    <!-- autocomplete input container -->
    <div class="form-autocomplete-input form-input">
      <!-- autocomplete real input box -->
      <input
        v-model="inputText"
        class="form-input"
        type="text"
        :placeholder="placeholder"
        @blur="closeSuggestions()"
      />
    </div>

    <!-- autocomplete suggestion list -->
    <ul v-if="suggestions.length" class="menu">
      <!-- menu list items -->
      <li
        v-for="suggestion in suggestions"
        :key="suggestion.id"
        class="menu-item"
      >
        <a href="#" @click.prevent="fillIn(suggestion)">
          <div class="tile tile-centered">
            <div v-if="itemsAreObjects" class="tile-content">
              {{ suggestion[attribute] }}
            </div>
            <div v-else class="tile-content">{{ suggestion }}</div>
          </div>
        </a>
      </li>
    </ul>
  </div>
</template>

<script>
import fuzzaldrin from "fuzzaldrin"

export default {
  name: "AutoComplete",
  props: {
    items: {
      type: Array,
      required: true
    },
    itemsAreObjects: {
      // if the items are objects or strings
      type: Boolean,
      default: false
    },
    attribute: {
      // if the items are objects, the attribute specifies to attribute to look for when filtering
      type: String,
      default: "name"
    },
    placeholder: {
      type: String,
      default: "Type here ..."
    }
  },
  data: function() {
    return {
      inputText: "",
      suggestions: []
    }
  },
  watch: {
    inputText: function(text) {
      const self = this
      if (self.itemsAreObjects) {
        this.suggestions = fuzzaldrin.filter(self.items, text, {
          key: self.attribute
        })
      } else {
        this.suggestions = fuzzaldrin.filter(self.items, text)
      }
      this.$emit("input", this.inputText)
    }
  },
  methods: {
    fillIn: function(suggestion) {
      if (this.itemsAreObjects) {
        this.inputText = suggestion[this.attribute]
      } else {
        this.inputText = suggestion
      }
    },
    closeSuggestions: function() {
      const self = this
      setTimeout(() => (self.suggestions = []), 50)
    }
  }
}
</script>

<style scoped></style>
