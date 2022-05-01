<template>
  <div
    :id="'feedback_' + feedback.id"
    class="feedback-item"
    :class="{ highlight: $route.hash === '#feedback_' + feedback.id }"
  >
    <div v-if="!feedback.draft" class="column col-12 tile">
      <div class="tile-icon">
        <reputation-card :user="feedback.reviewer">
          <avatar :user="feedback.reviewer"></avatar>
        </reputation-card>

        <div
          v-if="
            currentUser.id === feedback.receiver.id && feedback.type !== 'igr'
          "
          class="my-2"
        >
          <span
            v-if="feedback.rating === null"
            class="btn btn-action btn-link btn-sm tooltip tooltip-right"
            data-tooltip="Rate this Feedback"
            @click.prevent="showRatingPanel = !showRatingPanel"
          >
            <octicon name="star" class="icon text-warning" scale="1.5"></octicon
            ><br />
            Rate
          </span>
          <span
            v-else
            class="btn btn-action btn-link btn-sm tooltip tooltip-right"
            data-tooltip="You have rated this feedback"
            @click.prevent="showRatingPanel = !showRatingPanel"
          >
            <octicon
              name="check"
              class="icon text-success"
              scale="1.5"
            ></octicon
            ><br />Rated
          </span>
        </div>
      </div>
      <div class="tile-content">
        <div class="columns">
          <div
            class="column"
            :class="{ 'col-8 col-sm-7': feedback.grades.length > 0 }"
          >
            <div class="tile-title text-gray">
              {{ feedback.reviewer.name }}
              <span
                v-if="feedback.type === 'TA'"
                class="label label-rounded label-success"
              >
                {{ feedback.type }}
              </span>
            </div>
          </div>
          <div class="column col-4 col-sm-5 text-right">
            <p
              v-if="role === 'teacher' || role === 'ta'"
              class="d-inline px-2 text-large"
            >
              AI rating:
              <span v-if="feedback.ml_rating === 0"> &#x1f44e;</span>
              <span v-else-if="feedback.ml_rating === 1"> &#x1F610;</span>
              <span v-else-if="feedback.ml_rating === 2"> &#x1f44d;</span>
              <span v-else> Not Calculated</span>
            </p>
            <p v-if="feedback.grades.length && !rubricLoading" class="d-inline">
              <span
                @click="
                  $emit(
                    'show-rubric-with-grades',
                    feedback.rubric_id,
                    feedback.grades
                  )
                "
              >
                <span class="chip hide-sm c-hand">
                  <span
                    class="avatar avatar-sm"
                    :data-initial="totalPoints"
                    style="background-color: #5755d9;"
                  ></span>
                  Points
                </span>
                <a class="btn btn-link hide-sm">
                  <octicon name="unfold" scale="1.2" class="icon"></octicon>
                  Show Rubric
                </a>
              </span>
            </p>
          </div>
          <div class="column col-12 pt-2" v-html="content"></div>

          <div
            v-if="
              currentUser.id === feedback.receiver.id &&
                feedback.type !== 'igr' &&
                showRatingPanel
            "
            class="column col-12"
          >
            <feedback-item-rating-panel
              :feedback="feedback"
              @close-rating-panel="showRatingPanel = false"
            ></feedback-item-rating-panel>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { initials } from "../../utils/index"
import marked from "marked"
import { mapGetters, mapState } from "vuex"
import FeedbackItemRatingPanel from "./FeedbackItemRatingPanel"
import Octicon from "vue-octicon/components/Octicon"
import "vue-octicon/icons/star"
import "vue-octicon/icons/unfold"
import "vue-octicon/icons/check"
import Avatar from "../ui/Avatar"
import ReputationCard from "../ui/ReputationCard"

export default {
  name: "FeedbackItem",
  components: {
    FeedbackItemRatingPanel,
    Octicon,
    Avatar,
    ReputationCard
  },
  props: {
    feedback: {
      type: Object,
      required: true
    }
  },
  data: function() {
    return {
      showRatingPanel: false
    }
  },
  computed: {
    ...mapGetters("user", ["currentUser"]),
    ...mapGetters("rubric", ["rubricWithId"]),
    ...mapGetters("course", ["role"]),
    ...mapState({
      rubricLoading: state => state.rubric.isLoading
    }),
    totalPoints: function() {
      let rubric = this.rubricWithId(this.feedback.rubric_id)
      if (
        typeof rubric === "undefined" ||
        !Array.isArray(rubric.criterions) ||
        rubric.criterions.length !== this.feedback.grades.length
      )
        return 0

      let score = 0
      const vm = this
      vm.feedback.grades.forEach(function(grade, i) {
        let criteria = rubric.criterions[i]
        score += criteria.levels[grade.level].points
      })

      return score
    },
    content: function() {
      return marked(this.feedback.value)
    }
  },
  created() {
    if (this.feedback.rubric_id) {
      this.$store.dispatch(
        "rubric/getRubricWithCriterions",
        this.feedback.rubric_id
      )
    }
  },
  methods: {
    initials
  }
}
</script>

<style scoped>
.table-narrow td {
  padding: 0.2rem 0.1rem;
}
.feedback-item {
  padding-bottom: 0.5rem;
  padding-top: 0.5rem;
}
.tile-title {
  margin-top: 0.2rem;
}
</style>
