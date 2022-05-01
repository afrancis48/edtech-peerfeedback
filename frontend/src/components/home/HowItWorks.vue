<template>
  <div class="video-container">
    <ul class="tab tab-block">
      <li class="tab-item c-hand" :class="{ active: tabInstructors }">
        <a @click="setInstructors">Instructors and TAs</a>
      </li>
      <li class="tab-item c-hand" :class="{ active: tabStudents }">
        <a @click="setStudents">Students</a>
      </li>
    </ul>
    <video class="video-responsive" :src="videoURL" controls>
      <source type="video/mp4" />
      Your browser does not support the video tag.
    </video>
    <ul class="step">
      <li
        v-for="step in currentSteps"
        :key="step.label"
        class="step-item"
        :class="{ active: step.active }"
      >
        <a
          class="tooltip c-hand"
          :data-tooltip="step.tooltip"
          @click="setStep(step, currentSteps)"
        >
          {{ step.label }}
        </a>
      </li>
    </ul>
  </div>
</template>

<script>
export default {
  name: "HowItWorks",
  data: function() {
    return {
      tabInstructors: true,
      tabStudents: false,
      videoId: "",
      currentSteps: {},
      steps: {
        instructor: [
          {
            label: "Initialize course",
            tooltip: "Login with Canvas and open the course",
            active: true,
            videoId: "t_FIOX2-8xk"
          },
          {
            label: "Create Rubric",
            tooltip: "Create or choose a rubric",
            active: false,
            videoId: "3Uv-PSdV2Qw"
          },
          {
            label: "Pair Students",
            tooltip: "Pair students or TAs",
            active: false,
            videoId: "VcGIVfDzVe8"
          },
          {
            label: "Download Feedback",
            tooltip: "Get feedback data in CSV format",
            active: false,
            videoId: "vziPZeQF-Qg"
          }
        ],
        student: [
          {
            label: "Provide Feedback",
            tooltip: "Provide feedback to your peers",
            active: true,
            videoId: "hwgy_uvPk50"
          },
          {
            label: "Read Feedback",
            tooltip: "Read the feedback you received",
            active: false,
            videoId: "hYY_mFWBTpY"
          },
          {
            label: "Rate Feedback",
            tooltip: "Let TAs know about feedback quality",
            active: false,
            videoId: "RkJ4SqRiu1w"
          },
          {
            label: "Earn Medals",
            tooltip: "Work through achievements",
            active: false,
            videoId: "m_kL0sd9wZY"
          }
        ]
      }
    }
  },
  computed: {
    videoURL: function() {
      return (
        "https://peerfeedback-videos.s3.amazonaws.com/" + this.videoId + ".webm"
      )
    }
  },
  mounted() {
    this.setInstructors()
  },
  methods: {
    setInstructors() {
      this.tabInstructors = true
      this.tabStudents = false
      this.currentSteps = this.steps.instructor
      this.videoId = this.currentSteps[0].videoId
    },
    setStudents() {
      this.tabInstructors = false
      this.tabStudents = true
      this.currentSteps = this.steps.student
      this.videoId = this.currentSteps[0].videoId
    },
    setStep(step, currentSteps) {
      this.videoId = step.videoId

      currentSteps.forEach(function(s) {
        s.active = false
      })

      step.active = true
    }
  }
}
</script>

<style lang="scss" scoped>
@import "../../../node_modules/spectre.css/src/variables.scss";

.video-container {
  margin-top: 4em;
  background: $dark-color;
  box-shadow: 0 3px 20px rgba(0, 0, 0, 0.4);
  padding-bottom: 0.3em;
}

.tab .tab-item.active a {
  border-bottom-color: $light-color;
  color: $light-color;
  font-weight: 600;
}
</style>
