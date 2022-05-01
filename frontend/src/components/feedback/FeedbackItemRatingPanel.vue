<template>
  <div class="meta-feedback">
    <div v-if="metaStatus === 'DONE'" class="panel">
      <div class="panel-header">
        <div class="panel-title h6">
          You rated this feedback
          <span class="label label-rounded" :class="ratingClass">{{
            labelOf(meta.points)
          }}</span>
          <a
            href="#"
            class="btn btn-clear float-right"
            aria-label="Close"
            role="button"
            @click.prevent="$emit('close-rating-panel')"
          ></a>
        </div>
      </div>
      <div class="panel-body">
        <div v-if="meta.comment.length">
          Your comment:
          <blockquote>{{ meta.comment }}</blockquote>
        </div>
        <p class="visibility">
          <octicon name="eye" class="icon"></octicon> Only visible to you and
          instructors
        </p>
      </div>
    </div>

    <div v-else class="panel">
      <div class="panel-header">
        <div class="panel-title">
          <a
            href="#"
            class="btn btn-clear float-right"
            aria-label="Close"
            role="button"
            @click.prevent="$emit('close-rating-panel')"
          ></a>
          <h6>Private Peer Feedback</h6>
          <p class="text-gray">
            This feedback is just for your instructor to see. We won't make it
            public.
          </p>
        </div>
      </div>
      <div class="panel-body">
        <div class="form-group columns">
          <div class="column col-4 col-md-6 col-sm-12">
            <label for="meta_points" class="form-label">
              How helpful was this review to you?
            </label>
          </div>
          <div class="column col-4 col-md-6 col-sm-12">
            <select
              id="meta_points"
              v-model="meta.points"
              name="meta_points"
              class="form-select"
            >
              <option value="" disabled>Choose one</option>
              <option
                v-for="item in ratings"
                :key="item.rating"
                :value="item.rating"
              >
                {{ item.label }}
              </option>
            </select>
          </div>
        </div>
        <div class="form-group">
          <textarea
            id="meta_comment"
            v-model="meta.comment"
            class="form-input"
            placeholder="Let your instructor know how useful was this feedback and how it could have been better."
            rows="3"
          >
          </textarea>
        </div>
      </div>
      <div class="panel-footer">
        <button
          class="btn btn-primary float-right"
          :class="{ 'btn-loading': metaStatus === 'SENDING' }"
          :disabled="meta.points === ''"
          @click="sendMetaFeedback()"
        >
          Send to Course Instructor
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { mapActions } from "vuex"
import Octicon from "vue-octicon/components/Octicon.vue"
import "vue-octicon/icons/eye"

export default {
  name: "FeedbackItemRatingPanel",
  components: {
    Octicon
  },
  props: {
    feedback: {
      type: Object,
      required: true
    }
  },
  data: function() {
    return {
      ratings: [
        { label: "Very Helpful", rating: 6 },
        { label: "Helpful", rating: 5 },
        { label: "Somewhat Helpful", rating: 4 },
        { label: "Neutral", rating: 3 },
        { label: "Somewhat Unhelpful", rating: 2 },
        { label: "Unhelpful", rating: 1 },
        { label: "Very Unhelpful", rating: 0 }
      ],
      meta: {
        points: "",
        comment: ""
      },
      metaStatus: "INIT"
    }
  },
  computed: {
    ratingClass: function() {
      return this.meta.points < 3
        ? "label-error"
        : this.meta.points > 3
        ? "label-success"
        : "label-secondary"
    }
  },
  created() {
    if (this.feedback.rating === null) return
    this.meta = this.feedback.rating
    this.metaStatus = "DONE"
  },
  methods: {
    ...mapActions("feedback", ["rateFeedback"]),
    sendMetaFeedback: function() {
      const self = this
      self.metaStatus = "SENDING"
      let data = self.meta
      data.feedback_id = self.feedback.id
      data.receiver_id = self.feedback.reviewer.id

      self
        .rateFeedback(data)
        .then(meta => {
          self.$toasted.success("Your comment has been noted.", {
            duration: 3000
          })
          self.meta = meta
          self.metaStatus = "DONE"
        })
        .catch(error => {
          self.$toasted.success("Comment couldn't be saved: " + error, {
            duration: 3000
          })
          self.metaStatus = "ERROR"
        })
    },
    labelOf: function(points) {
      let rating = this.ratings.find(r => r.rating === points)
      return rating.label
    }
  }
}
</script>

<style scoped>
.meta-feedback .panel {
  background-color: #f8f9fa;
  border-radius: 0.25rem;
}
.visibility {
  font-size: smaller;
}
</style>
