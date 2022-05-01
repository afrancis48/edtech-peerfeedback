<template>
  <section class="columns">
    <portal :to="smallScreen || oneColumn ? 'mobileGrader' : 'desktopGrader'">
      <div id="grading_area" class="mx-2">
        <feedback-grader :save-content="futureColumns" :view_only=view_only @saved="feedbackSaved" />
      </div>
    </portal>

    <portal
      v-if="!settings.intra_group_review"
      :to="smallScreen || oneColumn ? 'mobileViewer' : 'desktopViewer'"
    >
      <div id="submission_content" class="mx-2">
        <submission-viewer :submission="submission" :enable-timer="true" />
        <replace-task />
      </div>
    </portal>

    <!-- Desktop grader controls -->
    <div
      v-if="!settings.intra_group_review"
      v-show="!smallScreen"
      :class="{ 'full-width': !oneColumn }"
    >
      <div class="column col-12">
        <div class="btn-group">
          <button class="btn btn-default btn-sm mx-2" @click="toggleFullscreen">
            <octicon class="icon" name="screen-full" /> Focus mode
          </button>
        </div>
        <div class="btn-group control-group">
          <button
            class="btn btn-default btn-sm"
            :class="{ active: oneColumn }"
            @click="toggleColumnMode"
          >
            One Column
          </button>
          <button
            class="btn btn-default btn-sm"
            :class="{ active: !oneColumn }"
            @click="toggleColumnMode"
          >
            Two Column
          </button>
        </div>
      </div>
    </div>

    <fullscreen
      v-if="!settings.intra_group_review"
      ref="fullscreen"
      class="max-height"
      background="#ffffff"
      @change="fullscreenChange"
    >
      <!-- Mobile grader -->
      <div v-show="smallScreen || oneColumn" class="mobile-grader">
        <portal-target name="mobileViewer" />
        <portal-target name="mobileGrader" />
      </div>

      <!-- Desktop grader -->
      <split
        v-show="!smallScreen && !oneColumn"
        :gutter-size="14"
        :class="{ 'full-width desktop-grader': !fullscreen }"
        class="columns"
      >
        <split-area :size="57" :min-size="300" class="left-feedback-block-pad">
          <portal-target name="desktopViewer" />
        </split-area>
        <split-area :size="43" :min-size="350" class="right-feedback-block-pad">
          <portal-target name="desktopGrader" />
        </split-area>
      </split>
    </fullscreen>

    <!-- show only the grading area for Intra Group Reviews -->
    <portal-target v-else name="desktopGrader" />
  </section>
</template>

<script>
import { mapState } from "vuex"
import FeedbackGrader from "./FeedbackGrader"
import SubmissionViewer from "./SubmissionViewer"
import Octicon from "vue-octicon/components/Octicon"
import "vue-octicon/icons/screen-full"
import ReplaceTask from "./ReplaceTask"

export default {
  name: "FeedbackWriter",
  components: {
    FeedbackGrader,
    SubmissionViewer,
    Octicon,
    ReplaceTask
  },
  props: {
    submission: {
      type: Object,
      required: true
    },
    view_only: {
      type: String,
      required: false,
      default: "false"
    }
  },
  data: function() {
    let oneColumn
    if (this.view_only === "true")
      oneColumn =  true
    else oneColumn = false
    return {
      oneColumn: oneColumn,
      smallScreen: false,
      fullscreen: false,
      futureColumns: 2
    }
  },
  computed: {
    ...mapState("assignment", ["settings"])
  },
  mounted() {
    window.addEventListener("resize", this.checkScreen)
  },
  beforeDestroy() {
    window.removeEventListener("resize", this.checkScreen)
  },
  methods: {
    toggleColumnMode: function() {
      this.futureColumns = this.futureColumns === 1 ? 2 : 1
    },
    checkScreen: function() {
      this.smallScreen =
        /Android|iPhone|iPad|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
        window.innerWidth < 960
    },
    toggleFullscreen: function() {
      this.$refs["fullscreen"].toggle()
    },
    fullscreenChange: function(fullscreen) {
      this.fullscreen = fullscreen
    },
    feedbackSaved: function() {
      if (this.futureColumns === 2 && this.oneColumn) {
        this.oneColumn = false
      }
      if (this.futureColumns === 1 && !this.oneColumn) {
        this.oneColumn = true
      }
    }
  }
}
</script>

<style scoped>
.full-width {
  width: 96vw;
  transform: translateX(calc((65em - 100vw) / 2));
}

.max-height {
  height: 100%;
}

.left-feedback-block-pad {
  padding-right: 2em;
}

.right-feedback-block-pad {
  padding-left: 2em;
}

.mobile-grader {
  margin-top: 1em;
}

.desktop-grader {
  margin-top: 1em;
}
</style>
