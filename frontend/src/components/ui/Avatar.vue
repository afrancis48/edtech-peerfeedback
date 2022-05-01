<template>
  <router-link
    v-if="link"
    :to="{ name: 'public-profile', params: { id: user.id } }"
  >
    <figure
      class="avatar"
      :class="sizeClass"
      :data-initial="initials(user.name)"
    >
      <img
        v-if="showImage && user.avatar_url"
        :src="user.avatar_url"
        @error="imageLoadFailed()"
      />
    </figure>
  </router-link>
  <figure
    v-else
    class="avatar"
    :class="sizeClass"
    :data-initial="initials(user.name)"
  >
    <img
      v-if="showImage && user.avatar_url"
      :src="user.avatar_url"
      @error="imageLoadFailed()"
    />
  </figure>
</template>

<script>
import { initials } from "../../utils"

export default {
  name: "Avatar",
  props: {
    user: {
      type: Object,
      required: true
    },
    size: {
      type: String,
      default: ""
    },
    link: {
      type: Boolean,
      default: true
    }
  },
  data: function() {
    return {
      showImage: true
    }
  },
  computed: {
    sizeClass: function() {
      switch (this.size) {
        case "huge":
          return "avatar-xl" // 64px
        case "big":
          return "avatar-lg" // 48px
        case "small":
          return "avatar-sm" // 24px
        case "tiny":
          return "avatar-xs" // 16px
        default:
          return "" // 32px
      }
    }
  },
  mounted: function() {
    if (this.user.avatar_url) {
      var defaultCanvasProfilePic = "avatar-50"

      if (this.user.avatar_url.indexOf(defaultCanvasProfilePic) !== -1) {
        this.showImage = false
      }
    }
  },
  methods: {
    initials,
    imageLoadFailed: function() {
      this.showImage = false
    }
  }
}
</script>
