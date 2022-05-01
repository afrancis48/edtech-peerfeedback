<template>
  <ul class="pagination">
    <li class="page-item" :class="{ disabled: pageIndex === 1 }">
      <a tabindex="-1" href="#" @click.prevent="gotoPrevious()">
        <Octicon name="chevron-left" scale="1.3" />
      </a>
    </li>

    <li
      v-for="(page, index) in pageButtons"
      :key="index"
      class="page-item"
      :class="{ active: page === pageIndex }"
    >
      <a href="#" @click.prevent="gotoPage(page)"> {{ page }} </a>
    </li>

    <li class="page-item" :class="{ disabled: pageIndex === pages }">
      <a tabindex="-1" href="#" @click.prevent="gotoNext()">
        <Octicon name="chevron-right" scale="1.3" />
      </a>
    </li>
  </ul>
</template>

<script>
import Octicon from "vue-octicon/components/Octicon"
import "vue-octicon/icons/chevron-left"
import "vue-octicon/icons/chevron-right"

export default {
  name: "Pagination",
  components: {
    Octicon
  },
  props: {
    pages: {
      type: Number,
      required: true
    },
    perPage: {
      type: Number,
      default: 10
    },
    currentPage: {
      // an optional prop to force update a current page
      type: Number,
      required: false,
      default: 1
    }
  },
  data: function() {
    return {
      pageIndex: 1
    }
  },
  computed: {
    pageButtons: function() {
      let idx = this.pageIndex
      if (this.pages <= 4) {
        return Array.from({ length: this.pages }, (v, k) => k + 1)
      }
      if (idx < 3) {
        return [1, 2, 3, "...", this.pages]
      } else {
        if (idx + 2 < this.pages) {
          return [1, "...", idx - 1, idx, idx + 1, "...", this.pages]
        } else {
          return [1, "...", this.pages - 2, this.pages - 1, this.pages]
        }
      }
    }
  },
  watch: {
    perPage: function() {
      // reset to first page when per page changes
      this.pageIndex = 1
    },
    currentPage: function() {
      this.pageIndex = this.currentPage
    }
  },
  methods: {
    gotoPrevious: function() {
      if (this.pageIndex > 1) this.pageIndex--
      this.$emit("goto", this.pageIndex)
    },
    gotoNext: function() {
      if (this.pageIndex < this.pages) this.pageIndex++
      this.$emit("goto", this.pageIndex)
    },
    gotoPage: function(page) {
      if (Number.isInteger(page)) this.pageIndex = page
      this.$emit("goto", this.pageIndex)
    }
  }
}
</script>

<style scoped></style>
