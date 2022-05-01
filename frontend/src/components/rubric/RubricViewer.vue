<template>
  <section>
    <h2>{{ rubric.name }}</h2>
    <p>{{ rubric.description }}</p>

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
          v-for="criteria in rubric.criterions"
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
                :class="columnSize"
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
        <!-- ./ criterias -->
      </div>
    </div>
    <!-- ./panel -->

    <div class="tile pt-2">
      <div class="tile-content">
        <p><strong>Maximum Score:</strong> {{ maxScore }}</p>
      </div>
    </div>
  </section>
</template>

<script>
export default {
  name: "RubricViewer",
  props: {
    rubric: {
      type: Object,
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
    columnSize: function() {
      let maxlevels = 0
      for (let criteria of this.rubric.criterions) {
        if (criteria.levels.length > maxlevels)
          maxlevels = criteria.levels.length
      }
      if (maxlevels > 3) return "col-3"
      return "col-" + 12 / maxlevels
    }
  }
}
</script>

<style lang="scss" scoped>
@import "../../../node_modules/spectre.css/src/variables";

.row-head {
  background-color: $light-color;
  border-right: $border-width-lg solid $border-color-dark;
  border-bottom: $border-width solid $border-color;
  h6 {
    margin-top: 0.5rem;
    margin-bottom: 0.75rem;
    font-weight: bold;
  }
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
  h6 {
    text-transform: uppercase;
    font-weight: bold;
  }
}

.clear-margins {
  margin-left: 0;
  margin-right: 0;
}
</style>
