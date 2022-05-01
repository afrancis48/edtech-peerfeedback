<template>
  <div class="panel mt-1">
    <div :value="criteria" @input="$emit('input', $event.target.value)">
      <div class="columns">
        <div class="column col-sm-12 col-3 pt-1 bg-dark rounded">
          <p class="chip">
            <small><strong>Name</strong></small>
          </p>
          <button
            class="btn btn-sm btn-link float-right"
            @click="$emit('remove')"
          >
            <i class="icon icon-cross text-error"></i>
          </button>
          <input
            v-model="criteria.name"
            class="form-input"
            type="text"
            placeholder="Criteria Name"
            data-test="criteria-name"
          />
          <p class="chip">
            <small><strong>Description</strong></small>
          </p>
          <textarea
            v-model="criteria.description"
            class="form-input"
            placeholder="Description"
            rows="3"
            data-test="criteria-desc"
          >
          </textarea>
          <p class="chip">
            <small><strong>Maximum Points</strong></small>
          </p>
          <div class="text-center form-input">{{ maxPoints }}</div>
          <p>
            <button
              class="btn btn-success btn-sm btn-block"
              data-test="add-level"
              @click="addLevel()"
            >
              <i class="icon icon-plus"></i> Add a Level
            </button>
          </p>
        </div>

        <div class="column col-9">
          <transition-group
            tag="div"
            class="columns"
            name="levels-transition"
            enter-active-class="animated zoomIn"
            leave-active-class="animated zoomOut"
          >
            <div
              v-for="level in criteria.levels"
              :key="level.position"
              class="column col-4 card"
              :data-test="'level_' + level.position"
            >
              <p class="text-center">
                Level {{ level.position + 1 }}
                <button
                  class="btn btn-link btn-sm float-right"
                  @click="removeLevel(level.position)"
                >
                  <i class="icon icon-cross text-gray"></i>
                </button>
              </p>
              <p class="label">
                <small><strong>Points</strong></small>
              </p>
              <input
                v-model.number="level.points"
                class="form-input"
                type="number"
                placeholder="0"
              />
              <p class="label">
                <small><strong>Descriptor</strong></small>
              </p>
              <textarea
                v-model="level.text"
                class="form-input"
                placeholder="Descriptor"
                rows="7"
              ></textarea>
            </div>
          </transition-group>
        </div>

        <div></div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "RubricCriteria",
  props: {
    criteria: {
      type: Object,
      required: true
    }
  },
  computed: {
    maxPoints: function() {
      let max = 0
      for (let level of this.criteria.levels) {
        if (parseFloat(level.points) > max) max = parseFloat(level.points)
      }
      return max
    }
  },
  created() {
    if (this.criteria.levels.length === 0) {
      this.criteria.levels.push({
        position: 0,
        text: "",
        points: 5
      })
    }
  },
  methods: {
    addLevel: function() {
      const position = this.criteria.levels.length
      this.criteria.levels.push({ position: position, text: "", points: null })
    },
    removeLevel: function(position) {
      if (this.criteria.levels.length === 1) {
        this.$toasted.error(
          "At least 1 level of grading is required per criteria.",
          { duration: 5000 }
        )
        return
      }
      this.criteria.levels.splice(position, 1)
      for (let level of this.criteria.levels) {
        if (position < level.position) {
          level.position--
        }
      }
    }
  }
}
</script>

<style scoped>
p {
  margin-top: 0.5rem;
  margin-bottom: 0.25rem;
}

.table td {
  border: 0;
  border-right: 1px solid #e7e9ed;
  vertical-align: top;
}
</style>
