<template>
  <div>
    <h2>Task Status</h2>
    <content-placeholders v-if="loadingData"></content-placeholders>
    <bar-graph
      v-if="metrics"
      :chart-data="chartData"
      :options="options"
    ></bar-graph>
    <div
      v-if="
        assignment.group_category_id &&
          !assignment.intra_group_peer_reviews &&
          pageCount > 0
      "
      class="panel"
    >
      <div class="panel-header text-center">
        <div class="panel-title h5 mt-10">
          Distribution of participation from each team
        </div>
      </div>
      <scatter-graph
        v-if="Object.keys(groupData).length > 0"
        :chart-data="distributionChartData"
        :options="percentDataOptions"
      ></scatter-graph>
    </div>
    <div v-if="feedbackData.length > 0" class="panel m-b-2">
      <div class="panel-header text-center">
        <div class="panel-title h5 mt-10">
          Distribution of the average total peer feedback points received by
          each student
        </div>
      </div>
      <div>
        <div class="panel-body">
          <scatter-graph
            :chart-data="analyticsChartData"
            :options="analyticsChartDataOptions"
          ></scatter-graph>
        </div>
      </div>
    </div>
    <div v-else class="panel">
      <div class="panel-header text-center">
        <div class="panel-title h5 mt-10">
          Sample Distribution of the average total peer feedback points received
          by each student
        </div>
      </div>
      <div>
        <div class="panel-body">
          <scatter-graph
            :chart-data="sampleAnalyticsChartData"
            :options="analyticsChartDataOptions"
          ></scatter-graph>
        </div>
      </div>
    </div>
    <div v-if="feedbackData.length > 0" class="panel">
      <div class="panel-header text-center">
        <div class="panel-title h5 mt-10">Rubric Breakdown</div>
      </div>
      <div>
        <div class="panel-body">
          <bar-graph
            :chart-data="rubricChartData"
            :options="chartDataOptions"
          ></bar-graph>
        </div>
        <div v-if="isChartTableDataLoaded" class="panel-body">
          <table class="table table-striped table-hover table-condensed">
            <thead>
              <tr>
                <th>Ratings</th>
                <th
                  v-for="(rubricCriteria, index) in rubricChartData.labels"
                  :key="index"
                >
                  {{ rubricCriteria }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(dataset, index) in rubricChartData.datasets"
                :key="index"
              >
                <td>{{ dataset.label }}</td>
                <td v-for="(data, i) in dataset.data" :key="i">
                  <span v-if="data != 0">
                    {{ rubricPercentage(data, totalStudents) }}
                  </span>
                  <span v-else> - </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
    <div v-else class="panel">
      <div class="panel-header text-center">
        <div class="panel-title h5 mt-10">Sample Rubric Breakdown</div>
      </div>
      <div>
        <div class="panel-body">
          <bar-graph
            :chart-data="sampleRubricChartData"
            :options="chartDataOptions"
          ></bar-graph>
        </div>
        <div class="panel-body">
          <table class="table table-striped table-hover table-condensed">
            <thead>
              <tr>
                <th>Ratings</th>
                <th
                  v-for="rubricCriteria in sampleRubricChartData.labels"
                  :key="`rating-${rubricCriteria}`"
                >
                  {{ rubricCriteria }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(dataset, index) in sampleRubricChartData.datasets"
                :key="index"
              >
                <td>{{ dataset.label }}</td>
                <td v-for="(data, i) in dataset.data" :key="i">
                  <span v-if="data != 0">
                    {{ rubricPercentage(data, sampleTotalStudents) }}
                  </span>
                  <span v-else> - </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import _ from "lodash"
import BarGraph from "@/components/ui/BarGraph"
import ScatterGraph from "@/components/ui/ScatterGraph"
import { mapState } from "vuex"

import FeedbackAPI from "../../api/feedback.js"
import CourseAPI from "../../api/course.js"
import PairingAPI from "../../api/pairing.js"
export default {
  name: "AssignmentTaskMetrics",
  components: {
    BarGraph,
    ScatterGraph
  },
  data: function() {
    return {
      totalStudents: 0,
      feedbackData: {},
      groupData: {},
      CHART_COLORS: {
        red: "rgb(255, 99, 132)",
        orange: "rgb(255, 159, 64)",
        yellow: "rgb(255, 205, 86)",
        green: "rgb(75, 192, 192)",
        blue: "rgb(54, 162, 235)",
        purple: "rgb(153, 102, 255)",
        grey: "rgb(201, 203, 207)",
        golden: "rgb(184,134,11)",
        pink: "rgb(255,20,147)",
        brown: "rgb(139,69,19)",
        maroon: "rgb(149,69,53)"
      },
      isChartTableDataLoaded: true,
      chartDataOptions: {
        scales: {
          yAxes: [
            {
              ticks: {
                beginAtZero: true,
                precision: 0
              }
            }
          ]
        }
      },
      percentDataOptions: {
        scales: {
          xAxes: [
            {
              ticks: {
                beginAtZero: true,
                precision: 0,
                max: 100
              }
            }
          ],
          yAxes: [
            {
              ticks: {
                beginAtZero: true,
                precision: 0,
                max: 0
              }
            }
          ]
        }
      },
      analyticsChartDataOptions: {
        scales: {
          xAxes: [
            {
              ticks: {
                beginAtZero: true,
                precision: 0,
                max: 0
              }
            }
          ],
          yAxes: [
            {
              ticks: {
                beginAtZero: true,
                precision: 0
              }
            }
          ]
        }
      },
      sampleTotalStudents: 50
    }
  },
  computed: {
    ...mapState("assignment", ["settings", "settingsLoading"]),
    ...mapState({
      loadingData: state => state.assignment.metricsLoading,
      metrics: state => state.assignment.metrics,
      rubric: state => state.rubric.current,
      assignment: state => state.assignment.current,
      settings: state => state.assignment.settings,
      pageCount: state => state.pairing.pageCount
    }),
    chartData() {
      return {
        labels: [
          "Pending " + this.percentOf("pending"),
          "In Progress " + this.percentOf("in_progress"),
          "Completed" + this.percentOf("completed"),
          "Archived" + this.percentOf("archived")
        ],
        datasets: [
          {
            label: "Tasks",
            data: [
              this.metrics.pending,
              this.metrics.in_progress,
              this.metrics.completed,
              this.metrics.archived
            ],
            fill: false,
            backgroundColor: [
              "rgba(255, 159, 64, 0.2)",
              "rgba(255, 205, 86, 0.2)",
              "rgba(75, 192, 192, 0.2)",
              "rgba(255, 99, 132, 0.2)"
            ],
            borderColor: [
              "rgb(255, 159, 64)",
              "rgb(255, 205, 86)",
              "rgb(75, 192, 192)",
              "rgb(255, 99, 132)"
            ],
            borderWidth: 1
          }
        ]
      }
    },
    sampleRubricChartData() {
      let sampleLabels = ["Criteria1", "Criteria2", "Criteria3"]
      let sampleDatasets = [
        {
          label: "rating1",
          data: [5, 10, 2],
          fill: true,
          backgroundColor: this.CHART_COLORS.red,
          borderColor: this.CHART_COLORS.red,
          borderWidth: 1
        },
        {
          label: "rating2",
          data: [15, 0, 23],
          fill: true,
          backgroundColor: this.CHART_COLORS.orange,
          borderColor: this.CHART_COLORS.orange,
          borderWidth: 1
        },
        {
          label: "rating3",
          data: [3, 20, 18],
          fill: true,
          backgroundColor: this.CHART_COLORS.green,
          borderColor: this.CHART_COLORS.green,
          borderWidth: 1
        }
      ]
      return {
        labels: sampleLabels,
        datasets: sampleDatasets
      }
    },
    rubricChartData() {
      const NAMED_COLORS = [
        this.CHART_COLORS.red,
        this.CHART_COLORS.orange,
        this.CHART_COLORS.yellow,
        this.CHART_COLORS.green,
        this.CHART_COLORS.blue,
        this.CHART_COLORS.purple,
        this.CHART_COLORS.grey,
        this.CHART_COLORS.golden,
        this.CHART_COLORS.pink,
        this.CHART_COLORS.brown,
        this.CHART_COLORS.maroon
      ]
      let rubricCriteriaData = []
      let index = 0
      // Get all possible ratings from rubric criteria
      let possibleRatings = []
      let labels = this.rubric.criterions.map(rubricCriteria => {
        rubricCriteria.levels.map(level => {
          if (!possibleRatings.includes(level.points)) {
            possibleRatings.push(level.points)
          }
        })
        return rubricCriteria.name
      })
      possibleRatings.sort(function(rating1, rating2) {
        return rating1 - rating2
      })

      // Get rubric criteria data with assigned students
      this.rubric.criterions.map(rubricCriteria => {
        let data = {
          id: index,
          criteria: rubricCriteria.name
        }
        rubricCriteria.levels.map(level => {
          let key = level.points
          data[key] = 0
        })
        Object.keys(this.feedbackData).map(feedback => {
          let grade = this.feedbackData[feedback].grades.find(
            g => g.criteria_id === rubricCriteria.id
          )
          let points = rubricCriteria.levels.find(
            level => level.position === grade.level
          ).points
          data[points] += 1
        })
        rubricCriteriaData.push(data)
      })

      // Convert the data to show into graph
      let points = {}
      possibleRatings.map(rating => {
        points[rating] = []
        rubricCriteriaData.map(rubricCriteria => {
          let studentCount = rubricCriteria[rating] ? rubricCriteria[rating] : 0
          points[rating].push(studentCount)
        })
      })
      let dataSet = []
      let total_colors = NAMED_COLORS.length
      Object.keys(points).map((key, index) => {
        let data = {
          label: key,
          data: points[key],
          fill: true,
          backgroundColor: NAMED_COLORS[index % total_colors],
          borderColor: NAMED_COLORS[index % total_colors],
          borderWidth: 1
        }
        dataSet.push(data)
      })
      return {
        labels: labels,
        datasets: dataSet
      }
    },
    distributionChartData() {
      let total_groups = Object.keys(this.groupData).length
      this.maxYValue(total_groups)
      let data = []
      Object.keys(this.groupData).map(groups => {
        let total_students = 0
        let completed_feedback = 0
        this.groupData[groups].map(group => {
          let pair_students = group.pairing.length
          total_students += pair_students
          let pairing_status_completed = group.pairing
            .map(pair => pair.task.status)
            .filter(value => {
              return value === "COMPLETE"
            }).length
          completed_feedback += pairing_status_completed
        })
        if (completed_feedback) {
          let percentage_participant = (
            (completed_feedback / total_students) *
            100
          ).toFixed(2)
          let current_data = {
            x: percentage_participant,
            y: groups
          }
          data.push(current_data)
        }
      })
      let dataSet = [
        {
          label: ["percentage of participants"],
          data: data,
          fill: true,
          backgroundColor: this.CHART_COLORS.blue,
          borderColor: this.CHART_COLORS.blue,
          borderWidth: 1,
          radius: 5
        }
      ]
      return {
        datasets: dataSet
      }
    },
    sampleAnalyticsChartData() {
      // let labels = Array.from(Array(5).keys())
      let data = [
        {
          x: 0,
          y: 2
        },
        {
          x: 1,
          y: 5
        },
        {
          x: 2,
          y: 4
        },
        {
          x: 3,
          y: 8
        },
        {
          x: 4,
          y: 1
        }
      ]
      this.maxXValue(5)
      let dataSet = [
        {
          label: "Students",
          data: data,
          fill: true,
          backgroundColor: this.CHART_COLORS.blue,
          borderColor: this.CHART_COLORS.blue,
          borderWidth: 1
        }
      ]
      return {
        datasets: dataSet
      }
    },
    analyticsChartData() {
      let total_points = 0
      this.rubric.criterions.map(rubricCriteria => {
        rubricCriteria.levels
        const max_level = rubricCriteria.levels.reduce((prev, current) =>
          prev.points > current.points ? prev : current
        )
        total_points += max_level.points
      })
      this.maxXValue(total_points)
      let data = []
      let total_grades = []
      Object.keys(this.feedbackData).map(feedback => {
        let individual_grade = 0
        this.feedbackData[feedback].grades.map(g => {
          let rubricCriteria = this.rubric.criterions.find(
            criteria => criteria.id === g.criteria_id
          )
          if (rubricCriteria) {
            let points = rubricCriteria.levels.find(
              level => level.position === g.level
            ).points
            individual_grade += points
          }
        })
        total_grades.push(individual_grade)
      })
      let total_grades_data = _.countBy(total_grades)
      Object.keys(total_grades_data).map(grade => {
        let current_data = {
          x: grade,
          y: total_grades_data[grade]
        }
        data.push(current_data)
      })
      let dataSet = [
        {
          label: ["Students"],
          data: data,
          fill: true,
          backgroundColor: this.CHART_COLORS.blue,
          borderColor: this.CHART_COLORS.blue,
          borderWidth: 1,
          radius: 5
        }
      ]
      return {
        datasets: dataSet
      }
    },
    options() {
      return {}
    }
  },
  watch: {
    settingsLoading: function(now, then) {
      if (
        !now &&
        then &&
        this.settings.rubric_id &&
        this.settings.rubric_id != 0
      ) {
        this.$store.dispatch("rubric/setCurrent", this.settings.rubric_id)
      }
    }
  },
  created() {
    this.$store.dispatch("assignment/getTaskMetrics", this.$route.params)
    if (
      this.settings.hasOwnProperty("rubric_id") &&
      this.settings.rubric_id != 0 &&
      this.settings.assignment_id === this.$route.params.assignment_id
    ) {
      this.$store.dispatch("rubric/setCurrent", this.settings.rubric_id)
    } else {
      this.$store.dispatch("assignment/loadSettings", this.$route.params)
    }
    this.$store.dispatch("pairing/getPairingPage", {
      course_id: this.$route.params.course_id,
      assignment_id: this.$route.params.assignment_id,
      page: 1,
      per_page: 10
    })
    this.getAllStudents()
    this.getAllFedback()
    this.getAllGroups()
  },
  methods: {
    percentOf(category) {
      let total = Object.values(this.metrics).reduce((a, b) => a + b, 0)
      let percent = ((this.metrics[category] / total) * 100).toFixed(1)
      return ` - ${percent}%`
    },
    rubricPercentage(assignedStudents, totalStudents) {
      if (totalStudents === 0) {
        return 0
      }
      return ((assignedStudents / totalStudents) * 100).toFixed(5)
    },
    maxYValue(total_groups) {
      this.percentDataOptions.scales.yAxes[0].ticks.max = total_groups
    },
    maxXValue(total_points) {
      this.analyticsChartDataOptions = {
        ...this.analyticsChartDataOptions,
        ...{
          scales: {
            xAxes: [
              {
                ticks: {
                  beginAtZero: true,
                  precision: 0,
                  max: total_points
                }
              }
            ],
            yAxes: [
              {
                ticks: {
                  beginAtZero: true,
                  precision: 0
                }
              }
            ]
          }
        }
      }
    },
    getAllStudents() {
      const course_id = this.$route.params.course_id
      this.isChartTableDataLoaded = false
      CourseAPI.getStudents(
        course_id,
        response => {
          this.isChartTableDataLoaded = true
          this.totalStudents = response.length
        },
        err => {
          console.log(err.response)
        }
      )
    },
    getAllFedback() {
      const routeParams = this.$route.params
      FeedbackAPI.getAllFeedbacksForSubmission(
        routeParams,
        response => {
          this.feedbackData = response
        },
        err => {
          console.log(err.response)
        }
      )
    },
    getAllGroups() {
      const routeParams = this.$route.params
      PairingAPI.getAllGroups(
        routeParams,
        response => {
          this.groupData = response
        },
        err => {
          console.log(err.response)
        }
      )
    }
  }
}
</script>

<style scoped lang="scss">
.m-b-2 {
  margin-bottom: 2rem;
}
</style>
