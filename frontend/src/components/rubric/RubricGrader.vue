<template>
  <div class="my-2">
    <h2>Grading Rubric</h2>
    <p class="text-gray">
      This will <em>not</em> be used to calculate your classmate's grade
    </p>

    <content-placeholders v-if="rubricLoading">
      <content-placeholders-heading />
      <content-placeholders-text :lines="2" />
    </content-placeholders>

    <div v-if="!rubricLoading" class="panel rubric-grader">
      <div class="panel-body">
        <div class="columns no-margin">
          <div class="column col-3 rubric-header text-center">
            <h6>Criteria</h6>
          </div>
          <div class="column col-9 rubric-header text-center">
            <h6>Levels</h6>
          </div>
        </div>

        <div
          v-for="(criteria, index) in rubric.criterions"
          :key="criteria.id"
          class="columns no-margin criteria"
        >
          <div class="column col-3 text-center criteria-name">
            <span>{{ criteria.name }}</span>
            <p class="criteria-description">{{ criteria.description }}</p>
          </div>

          <div class="column col-9">
            <div class="columns full-height">
              <div
                v-for="level in criteria.levels"
                :key="level.id"
                class="column criteria-level"
                :class="{
                  'active-level': grades[index].level === level.position
                }"
              >
                <label class="form-radio criteria-level-radio full-height">
                  <input
                    :id="criteria.id + '_' + level.position"
                    type="radio"
                    :name="'criteria_' + criteria.id"
                    @click="setGrade(index, level.position)"
                  />
                  {{ level.text | truncate(10, "...", !showDescription) }}
                  <br />
                  <span class="nobr text-italic chip text-dark">
                    {{ level.points }} pts
                  </span>
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="panel-footer">
        <div class="form-group">
          <label class="form-switch form-inline">
            <input v-model="showDescription" type="checkbox" />
            <i class="form-icon"></i> Show full level descriptions
          </label>
        </div>
      </div>
    </div>
    <p>
      <span class="label my-2" :class="gradingStatus.style">
        {{ gradingStatus.label }}
      </span>
    </p>
  </div>
</template>

<script>
import { mapState, mapGetters } from "vuex"

export default {
  name: "RubricGrader",
  props: {
    rubricId: {
      type: Number,
      default: null
    },
    initialGrades: {
      type: Array,
      default: () => []
    }
  },
  data: function() {
    return {
      grades: [],
      showDescription: true
    }
  },
  computed: {
    ...mapGetters("rubric", ["rubricWithId"]),
    ...mapState({
      rubricLoading: state => state.rubric.isLoading,
      rubric: state => state.rubric.current
    }),
    gradingStatus: function() {
      let empty = this.grades.reduce(
        (acc, cur) => acc & (cur.level === null),
        true
      )
      if (empty) return { label: "Please start grading", style: "label-light" }

      let complete = this.grades.reduce(
        (acc, cur) => acc & Number.isInteger(cur.level),
        true
      )
      return complete
        ? { label: "Rubric is complete!", style: "label-success" }
        : { label: "Please complete the rubric", style: "label-warning" }
    }
  },
  created() {
    if (this.rubricWithId(this.rubricId)) {
      this.initGrades()
    } else {
      this.$store
        .dispatch("rubric/getRubricWithCriterions", this.rubricId)
        .then(() => this.initGrades())
    }
  },
  methods: {
    setGrade: function(criteria, level) {
      this.grades[criteria].level = level
      this.$emit("input", this.grades)
    },
    initGrades: function() {
      this.$store.commit("rubric/setAsCurrent", this.rubricId)
      // Initialize the grades array for storing the grades
      this.grades = this.rubric.criterions.map(c => ({
        criteria_id: c.id,
        criteria: c.name,
        level: null
      }))
      // If initial data is given, then update the grades with the init data
      // ensure it is the same rubric and not one with similar no of criteria alone
      if (this.initialGrades.length === this.rubric.criterions.length) {
        let sameRubric = this.initialGrades.reduce(
          (acc, cur, idx) =>
            acc && cur.criteria_id === this.rubric.criterions[idx].id,
          true
        )
        if (sameRubric) {
          this.grades = this.initialGrades
          this.$emit("input", this.initialGrades)
        }
      }
    }
  }
}
</script>

<style scoped lang="scss">
@import "../../../node_modules/spectre.css/src/variables";

.nobr {
  white-space: nowrap;
}

.rubric-header {
  border-top: $border-width solid $border-color;
  border-bottom: $border-width-lg solid $border-color-dark;
  padding-top: 0.5rem;
}
.rubric-header:nth-child(1) {
  border-right: $border-width solid $border-color;
}

.criteria {
  border-bottom: $border-width solid $border-color;
}
.criteria-name {
  padding-top: 0.5rem;
  font-size: small;
  border-right: $border-width solid $border-color;
}

.criteria-description {
  font-size: small;
  padding-left: 0.6em;
}

.panel > .panel-body {
  padding: 0;
}

.criteria-level-radio {
  padding: 0;
  font-size: small;
  width: 100%;
  cursor: pointer;
  line-height: 1rem;
}

.criteria-level:hover {
  background-color: $secondary-color !important;
}

.active-level {
  background-color: $primary-color;
  color: $light-color;

  .chip {
    color: $dark-color;
  }
}

.criteria-level.active-level:hover {
  cursor: default !important;
  background-color: $primary-color !important;
  color: $light-color !important;
}

.no-margin {
  margin-left: 0;
  margin-right: 0;
}

.full-height {
  height: 100%;
}

.rubric-grader {
  height: 40vh;
  resize: vertical;
  overflow: auto;
}
</style>
