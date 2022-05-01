<template>
  <main>
    <div class="columns">
      <div class="column col-3 col-xs-12"><h2>All Feedback</h2></div>
      <div class="column col-3 col-xs-12">
        <div class="form-group">
          <select
            id="sort_select"
            v-model="sort_by"
            name="sort_select"
            class="form-select select-sm"
            @change="refetchFeedbacks()"
          >
            <option value="newest">Newest First</option>
            <option value="oldest">Oldest First</option>
          </select>
        </div>
      </div>
      <div class="column col-3 col-xs-12">
        <div class="form-group">
          <select
            id="course_filter"
            v-model="course_id"
            title="Filter By Course"
            name="course_filter"
            class="form-select select-sm"
            @change="refetchFeedbacks()"
          >
            <option value="0">Filter By Course</option>
            <option
              v-for="course in courses"
              :key="course.id"
              :value="course.id"
            >
              {{ course.name }}
            </option>
          </select>
        </div>
      </div>
      <div class="column col-3 col-xs-12">
        <p v-if="feedbacks.length" class="text-gray text-right">
          Showing 1 - {{ feedbacks.length }} of {{ totalFeedback }}
        </p>
      </div>
    </div>

    <div class="divider"></div>

    <section v-if="feedbacks.length">
      <div
        v-for="fb in feedbacks"
        :key="fb.id"
        class="fb-item pt-2"
        @click="gotoDiscussion(fb)"
      >
        <div class="columns">
          <div class="column col-3 col-sm-12">
            <p>
              <avatar :user="fb.receiver" size="small"></avatar
              ><strong class="pl-1">{{ fb.receiver.name }}</strong>
            </p>
          </div>
          <div class="column col-8 col-sm-12">
            <p class="mb-0">{{ fb.course_name }} · {{ fb.assignment_name }}</p>
            <p class="text-ellipsis text-gray">{{ fb.value }}</p>
          </div>
          <div class="column col-1 col-sm-12">
            <p class="mb-0 text-right">
              <small>{{ fb.end_date | shortTime }}</small>
              {{ fb.end_date | shortDate }}
            </p>
          </div>
        </div>
      </div>
    </section>

    <empty-state
      v-if="!isLoading && !feedbacks.length"
      title="No feedback yet"
      message="You haven't reviewed any assignments and given feedback yet."
    ></empty-state>

    <content-placeholders v-if="isLoading">
      <content-placeholders-text />
      <content-placeholders-text />
    </content-placeholders>

    <button
      v-if="hasMore"
      class="btn btn-link btn-block pt-2"
      @click="loadMore()"
    >
      Load more
    </button>
  </main>
</template>

<script>
import { mapState } from "vuex"
import Avatar from "../components/ui/Avatar"
import { feedbackLink } from "../utils"
import EmptyState from "../components/ui/EmptyState"

export default {
  name: "MyFeedbacks",
  components: {
    Avatar,
    EmptyState
  },
  data: function() {
    return {
      course_id: 0,
      sort_by: "newest"
    }
  },
  computed: {
    ...mapState("feedback", [
      "hasMore",
      "currentPage",
      "totalFeedback",
      "isLoading"
    ]),
    ...mapState({
      feedbacks: state => state.feedback.all,
      courses: state => state.course.courses
    })
  },
  created() {
    this.$store.dispatch("feedback/getAllFeedback", { page: 1 })
    this.$store.dispatch("course/getCourses")
  },
  methods: {
    loadMore: function() {
      this.$store.dispatch("feedback/getAllFeedback", {
        page: this.currentPage + 1,
        course_id: this.course_id
      })
    },
    gotoDiscussion: function(feedback) {
      let page = this.$router.resolve(feedbackLink(feedback))
      window.open(page.href, "_blank")
    },
    refetchFeedbacks: function() {
      this.$store.dispatch("feedback/getAllFeedback", {
        page: 1,
        course_id: this.course_id,
        sort_by: this.sort_by
      })
    }
  }
}
</script>

<style scoped>
.fb-item {
  border-bottom: 1px solid #eee;
}
.fb-item:hover {
  border-top: 1px solid #ddd;
  border-bottom: 1px solid #ddd;
  box-shadow: 0 2px 2px -2px #999;
  cursor: pointer;
  background-color: #f8f8f8;
}
</style>
