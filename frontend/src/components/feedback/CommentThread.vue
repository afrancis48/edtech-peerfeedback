<template>
  <section>
    <h2 class="pt-2">Discuss Feedback</h2>

    <div class="panel comment-panel">
      <div v-if="commentsLoading" class="panel-body px-2">
        <content-placeholders v-for="n in 3" :key="'comment_ph_' + n">
          <content-placeholders-heading :img="true" />
          <content-placeholders-text :lines="1" />
        </content-placeholders>
      </div>

      <div v-if="comments.length" class="panel-body">
        <comment-item
          v-for="comment in comments"
          :key="comment.id"
          :comment="comment"
        ></comment-item>
      </div>
    </div>

    <div v-if="!commentsLoading">
      <markdown-editor
        v-if="!submittingComment"
        v-model="commentText"
        initial-text=""
      ></markdown-editor>
      <button
        class="btn btn-primary mt-2 float-right"
        :class="{ loading: submittingComment }"
        @click="submitComment()"
      >
        Comment
      </button>
    </div>
  </section>
</template>

<script>
import CommentItem from "./CommentItem"
import { mapActions, mapState } from "vuex"
import MarkdownEditor from "../ui/MarkdownEditor"

export default {
  name: "CommentThread",
  components: {
    CommentItem,
    MarkdownEditor
  },
  props: {
    submissionId: {
      type: Number,
      required: true
    }
  },
  data: function() {
    return {
      commentsLoaded: false,
      commentText: ""
    }
  },
  computed: {
    ...mapState({
      comments: state => state.comment.all,
      commentsLoading: state => state.comment.isLoading,
      submittingComment: state => state.comment.addingComment
    })
  },
  watch: {
    submittingComment: function(now, then) {
      if (!now && then) this.commentText = ""
    },
    commentsLoading: function(isLoading, wasLoading) {
      if (!isLoading && wasLoading) {
        const anchor = this.$route.hash
        if (anchor.indexOf("comment") === -1) return
        this.$nextTick(() => {
          if (anchor && document.querySelector(anchor)) {
            location.href = anchor
          }
        })
      }
    }
  },
  created() {
    this.$store.dispatch("comment/getComments", this.$route.params)
  },
  methods: {
    ...mapActions("comment", ["addComment"]),
    submitComment: function() {
      const self = this
      if (this.commentText.trim().length === 0) {
        this.$toasted.error("Enter some text to comment", { duration: 3000 })
        return
      }
      let data = {
        value: self.commentText,
        submission_id: self.submissionId,
        course_id: parseInt(self.$route.params.course_id),
        assignment_id: parseInt(self.$route.params.assignment_id),
        recipient_id: parseInt(self.$route.params.user_id)
      }

      try {
        self.addComment(data)
      } catch (e) {
        self.$toasted.error("Failed to post comment. " + e.statusText, {
          duration: 3000
        })
      }
    }
  }
}
</script>

<style scoped>
.comment-panel > .panel-body {
  padding: 0;
  overflow-y: visible;
}
</style>
