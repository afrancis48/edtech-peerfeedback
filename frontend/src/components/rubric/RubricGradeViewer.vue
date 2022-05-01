<template>
  <section>
    <h2>Grading</h2>

    <div class="panel">
      <div class="panel-body">
        <div class="columns clear-margins">
          <div class="column col-3 text-center row-head column-head">
            <h6 class="pt-2">Criteria</h6>
          </div>
          <div class="column col-9 text-center column-head">
            <h6 class="pt-2">Grades</h6>
          </div>
        </div>

        <div
          v-for="(criteria, cIndex) in rubric.criterions"
          :key="criteria.id"
          class="columns clear-margins"
        >
          <div class="column col-3 text-center row-head">
            <h6 class="pt-2">{{ criteria.name }}</h6>
            <p>{{ criteria.description }}</p>
          </div>

          <div class="column col-9 row" style="font-size: 0.7rem;">
            <div class="columns">
              <div
                v-for="level in criteria.levels"
                :key="level.id"
                class="column"
                :class="{ highlight: graded(cIndex, level), columnSize }"
              >
                <p>
                  {{ level.text }}<br />
                  <span class="chip text-primary">
                    {{ level.points }} pts
                  </span>
                </p>
              </div>
            </div>
          </div>
        </div>
        <div id="rubric-bottom" v-observe-visibility="atBottom"></div>
        <!-- ./ criterias -->
      </div>
    </div>
    <!-- ./panel -->

    <div class="tile pt-2">
      <div class="tile-content">
        <p><strong>Score:</strong> {{ totalScore }} out of {{ maxScore }}</p>
      </div>
    </div>
  </section>
</template>

<script>
import Vue from "vue"
import VueObserveVisibility from "vue-observe-visibility"

Vue.use(VueObserveVisibility)

export default {
  name: "RubricGradeViewer",
  props: {
    rubric: {
      type: Object,
      required: true
    },
    grades: {
      type: Array,
      required: true
    }
  },
  computed: {
    maxScore: function() {
      let score = 0
      for (let criteria of this.rubric.criterions) {
        let points = criteria.levels.map(level => parseFloat(level.points))
        score += Math.max(...points)
      }
      return score
    },
    totalScore: function() {
      let score = 0
      const vm = this

      let complete = vm.grades.reduce(
        (acc, cur) => acc & Number.isInteger(cur.level),
        true
      )
      if (!complete) return "Incomplete"

      vm.grades.forEach(function(grade, i) {
        let criteria = vm.rubric.criterions[i]
        score += criteria.levels[grade.level].points
      })

      return score
    },
    columnSize: function() {
      let maxlevels = 0
      for (let criteria of this.rubric.criterions) {
        if (criteria.levels.length > maxlevels)
          maxlevels = criteria.levels.length
      }
      if (maxlevels > 3) return "col-3"
      return "col-" + 12 / maxlevels
    }
  },
  methods: {
    graded: function(cIndex, level) {
      let levelGrade = this.grades[cIndex]
      return levelGrade && levelGrade.level === level.position
    },
    atBottom: function(isVisible) {
      if (isVisible) {
        this.$emit("rubric-bottom-visible")
      }
    }
  }
}
</script>

<style lang="scss" scoped>
@import "../../../node_modules/spectre.css/src/variables";

.highlight {
  background-color: $primary-color !important;
  color: $light-color !important;
}

.row-head {
  background-color: $light-color;
  border-right: $border-width-lg solid $border-color-dark;
  border-bottom: $border-width solid $border-color;
}

.panel > .panel-body {
  padding: 0;
}

.row {
  border-bottom: $border-width solid $border-color;
}

.column-head {
  background-color: $light-color;
  border-bottom: $border-width-lg solid $border-color-dark;
}

.clear-margins {
  margin-left: 0;
  margin-right: 0;
}
</style>
