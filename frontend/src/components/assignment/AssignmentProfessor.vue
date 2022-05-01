<template>
  <section>
    <div v-if="settingsNotExist" class="columns">
      <div class="column col-12">
        <div class="empty">
          <div class="empty-icon">
            <octicon name="rocket" scale="2"></octicon>
          </div>
          <p class="empty-title h5">Almost ready to start!</p>
          <p class="empty-subtitle">
            Please do a one time course initialization in order to start pairing
            students.
          </p>
          <div class="empty-action">
            <transition
              name="fade"
              mode="out-in"
              enter-active-class="animated fadeIn"
              leave-active-class="animated fadeOut"
            >
              <div v-if="job">
                <progress-bar
                  :job-id="job.id"
                  @job-completed="clearJob()"
                ></progress-bar>
              </div>

              <button
                v-if="!setupInProgress"
                class="btn btn-primary"
                data-test="initialize-course"
                @click="setupParentCourse()"
              >
                Initialize Course
              </button>
            </transition>
          </div>
        </div>
      </div>
      <div class="column col-12"></div>
    </div>
    <div v-if="!settingsNotExist" class="columns">
      <div class="column col-3 col-xs-12">
        <ul class="menu">
          <li class="menu-item">
            <router-link
              :to="{ name: 'assignment.settings', params: $route.params }"
            >
              <octicon name="settings" class="icon"></octicon> Settings
            </router-link>
          </li>
          <li class="menu-item">
            <router-link
              :to="{ name: 'assignment.pairing-table', params: $route.params }"
            >
              <octicon name="organization" class="icon"></octicon> Current Pairs
            </router-link>
          </li>
          <li class="menu-item">
            <router-link
              :to="{ name: 'assignment.pair', params: $route.params }"
            >
              <octicon name="link" class="icon"></octicon> Create Pairs
            </router-link>
          </li>
          <li class="menu-item">
            <router-link
              :to="{ name: 'assignment.rubric', params: $route.params }"
            >
              <octicon name="law" class="icon"></octicon> Rubric
            </router-link>
          </li>
          <li class="menu-item">
            <router-link
              :to="{ name: 'assignment.data', params: $route.params }"
            >
              <octicon name="desktop-download" class="icon"></octicon> Data
            </router-link>
          </li>
          <li class="menu-item">
            <router-link
              :to="{ name: 'assignment.metrics', params: $route.params }"
            >
              <octicon name="graph" class="icon"></octicon> Metrics
            </router-link>
          </li>
        </ul>
      </div>
      <div class="column col-9 col-xs-12"><router-view></router-view></div>
    </div>
  </section>
</template>

<script>
import { mapState, mapActions } from "vuex"
import "vue-octicon/icons/organization"
import "vue-octicon/icons/settings"
import "vue-octicon/icons/link"
import "vue-octicon/icons/law"
import "vue-octicon/icons/desktop-download"
import "vue-octicon/icons/rocket"
import "vue-octicon/icons/graph"
import Octicon from "vue-octicon/components/Octicon"
import ProgressBar from "../ui/ProgressBar"

export default {
  name: "AssignmentProfessor",
  components: {
    Octicon,
    ProgressBar
  },
  props: {
    course: {
      type: Object,
      required: true
    },
    assignment: {
      type: Object,
      required: true
    }
  },
  data: function() {
    return {
      job: false,
      setupInProgress: false
    }
  },
  computed: {
    ...mapState("course", ["students"]),
    ...mapState("assignment", ["settingsNotExist"])
  },
  created() {
    this.$store.dispatch("course/getStudents", this.course.id)
    this.$store.dispatch("assignment/loadSettings", this.$route.params)
    this.$store.dispatch("rubric/getAllRubrics")
  },
  methods: {
    ...mapActions("course", ["setupCourse"]),
    setupParentCourse: function() {
      const self = this
      let course_id = parseInt(self.$route.params.course_id)
      self.setupInProgress = true
      self
        .setupCourse(course_id)
        .then(job => {
          self.job = job
        })
        .catch(error => {
          self.setupInProgress = false
          let msg = error.statusText
          if (error.response.data.hasOwnProperty("message")) {
            msg = error.response.data.message
          }
          self.$toasted.error(msg, { duration: 500 })
        })
    },
    clearJob: function() {
      this.setupInProgress = false
      this.job = false
      this.$store.dispatch("assignment/loadSettings", this.$route.params)
      this.$store.dispatch("course/getStudents", this.course.id)
    }
  }
}
</script>

<style scoped>
.bottom-pad {
  margin-bottom: 3em;
}
.menu .menu-item > a.router-link-active {
  background: #f1f1fc;
  color: #5755d9;
}
</style>
