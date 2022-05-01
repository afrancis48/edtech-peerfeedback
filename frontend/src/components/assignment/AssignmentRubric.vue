<template>
  <section>
    <div class="columns">
      <div class="column col-12 mb-2">
        <router-link
          :to="{ name: 'rubric-manager' }"
          class="btn btn-default btn-sm float-right"
        >
          Manage Rubrics
        </router-link>
      </div>
    </div>
    <content-placeholders v-if="settingsLoading || rubricLoading">
      <content-placeholders-heading />
      <content-placeholders-text />
    </content-placeholders>

    <div
      v-if="!settingsLoading && settings.use_rubric && !rubricLoading"
      class="columns"
    >
      <div v-if="rubric.id" class="column col-12">
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

              <div class="column col-9 row">
                <div class="columns">
                  <div
                    v-for="level in criteria.levels"
                    :key="level.id"
                    class="column col-4"
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
      </div>
    </div>
    <div v-if="!settingsLoading && !settings.use_rubric" class="column col-12">
      <empty-state
        title="No Rubric"
        message="No rubric has been set for this assignment. Please set a rubric."
        action="Choose a rubric"
        @empty-action="
          $router.push({ name: 'assignment.settings', params: $route.params })
        "
      >
      </empty-state>
    </div>
  </section>
</template>

<script>
import { mapState } from "vuex"
import EmptyState from "../ui/EmptyState"
export default {
  name: "AssignmentRubric",
  components: {
    EmptyState
  },
  computed: {
    ...mapState("assignment", ["settings", "settingsLoading"]),
    ...mapState({
      rubric: state => state.rubric.current,
      rubricLoading: state => state.rubric.isLoading
    })
  },
  watch: {
    settingsLoading: function(now, then) {
      if (!now && then && this.settings.rubric_id) {
        this.$store.dispatch("rubric/setCurrent", this.settings.rubric_id)
      }
    }
  },
  created() {
    if (
      this.settings.hasOwnProperty("rubric_id") &&
      this.settings.assignment_id === this.$route.params.assignment_id
    ) {
      this.$store.dispatch("rubric/setCurrent", this.settings.rubric_id)
    } else {
      this.$store.dispatch("assignment/loadSettings", this.$route.params)
    }
  }
}
</script>

<style scoped lang="scss">
@import "../../../node_modules/spectre.css/src/variables";
.row-head {
  background-color: $light-color;
  border-right: $border-width-lg solid $border-color-dark;
  border-bottom: $border-width solid $border-color;
}

.panel > .panel-body {
  padding: 0;
  font-size: 0.7rem;
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
