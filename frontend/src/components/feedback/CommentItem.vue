<template>
  <div
    :id="'comment_' + comment.id"
    class="tile comment"
    :class="{ highlight: $route.hash === '#comment_' + comment.id }"
  >
    <div class="tile-icon">
      <avatar :user="comment.commenter" size="small"></avatar>
    </div>
    <div class="tile-content">
      <div class="columns">
        <div class="column col-10">
          <p class="tile-title text-gray">{{ comment.commenter.name }}</p>
          <div class="tile-subtitle" v-html="content"></div>
        </div>
        <div class="column col-2">
          <div class="text-right text-gray">
            <span class="heart">
              <small v-if="comment.likes.length">
                {{ comment.likes.length }}
              </small>
              <input
                :id="'heart' + comment.id"
                class="toggle-heart"
                type="checkbox"
                :checked="liked"
              />
              <label :for="'heart' + comment.id" @click.prevent="heartIt()">
                <octicon class="icon action-icon" name="heart"></octicon>
              </label>
            </span>
          </div>
          <div class="text-right">
            <span
              class="tooltip tooltip-left text-gray"
              :data-tooltip="likedUsers"
            >
              <octicon name="smiley" class="icon action-icon"></octicon>
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import Avatar from "../ui/Avatar"
import Octicon from "vue-octicon/components/Octicon"
import "vue-octicon/icons/heart"
import "vue-octicon/icons/smiley"
import { mapActions, mapGetters } from "vuex"
import marked from "marked"

export default {
  name: "Comment",
  components: {
    Avatar,
    Octicon
  },
  props: {
    comment: {
      type: Object,
      required: true
    }
  },
  computed: {
    ...mapGetters("user", ["currentUser"]),
    likedUsers: function() {
      return (
        this.comment.likes.map(like => like.user.name).join("\n") ||
        "Be the first to like this comment"
      )
    },
    userLike: function() {
      return this.comment.likes.find(
        like => like.user.id === this.currentUser.id
      )
    },
    liked: function() {
      return typeof this.userLike !== "undefined"
    },
    content: function() {
      return marked(this.comment.value)
    }
  },
  methods: {
    ...mapActions("comment", ["likeComment", "unlikeComment"]),
    heartIt: function() {
      if (this.currentUser.id === this.comment.commenter.id) return

      if (this.liked) {
        this.unlikeComment({
          like_id: this.userLike.id,
          comment_id: this.comment.id
        })
      } else {
        this.likeComment(this.comment.id)
      }
    }
  }
}
</script>

<style scoped>
@keyframes heart {
  0% {
    font-size: 0.7rem;
  }
  50% {
    font-size: inherit;
  }
  80% {
    font-size: 0.7rem;
  }
  100% {
    font-size: inherit;
  }
}

.heart {
  width: 2rem;
  justify-content: center; /* horizontal alignment */
  margin: 0;
}

.toggle-heart {
  position: absolute;
  left: -100vw;
}
.toggle-heart:hover + label {
  color: #5755d9;
}
.toggle-heart:checked + label {
  color: #e2264d;
  will-change: font-size;
  animation: heart 0.4s linear;
  background-color: transparent;
  border: 2px solid transparent;
}
.action-icon:hover {
  cursor: pointer;
}
.comment {
  border-bottom: 1px solid #f0f1f4;
  padding: 0.8em;
}
.comment > .tile-icon {
  padding: 0.3rem 0 0 0.3rem;
}
.comment > .tile-content {
  padding-top: 0.3rem;
  padding-bottom: 0.5rem;
}
.columns {
  margin-right: 0;
}
</style>
