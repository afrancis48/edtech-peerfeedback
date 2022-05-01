<template>
  <main>
    <div class="columns">
      <div class="column col-8"><h1>Rubric Creator</h1></div>
      <div class="column col-4">
        <button class="btn float-right" @click="showRubricList = true">
          Clone an Existing Rubric
        </button>
      </div>
      <div class="column col-6">
        <div class="form-group">
          <div class="columns">
            <label for="rubric_name" class="form-label column col-3">
              Rubric Name
            </label>
            <input
              id="rubric_name"
              ref="rname"
              v-model="rubric_name"
              class="form-input column col-9"
              type="text"
            />
          </div>
        </div>
        <div class="form-group">
          <div class="columns">
            <label for="description" class="form-label column col-3">
              Description
            </label>
            <textarea
              id="description"
              v-model="description"
              class="form-input column col-9"
            ></textarea>
          </div>
        </div>
      </div>

      <div class="column col-4 col-mx-auto">
        <div class="form-group">
          <label class="form-checkbox">
            <input v-model="makePublic" type="checkbox" />
            <i class="form-icon"></i>Make it Public
            <span
              class="tooltip"
              data-tooltip="Other users can use this rubric in their courses"
            >
              <octicon name="question"></octicon>
            </span>
          </label>
        </div>
      </div>

      <div class="column col-6 pt-2">
        <h6 class="pt-2">Assessment Criteria</h6>
      </div>

      <div v-if="criterions.length === 0" class="column col-12">
        <div class="empty">
          <div class="empty-icon"><i class="icon icon-flag"></i></div>
          <p class="empty-title h5">No Assessment Criteria Present</p>
          <p class="empty-subtitle">
            Click the button to start adding assessment criteria.
          </p>
          <div class="empty-action">
            <button class="btn btn-primary" @click="addCriteria()">
              Add Criteria
            </button>
          </div>
        </div>
      </div>

      <transition-group
        tag="div"
        class="column col-12"
        name="criteria-transition"
        enter-active-class="animated fadeInLeft"
        leave-active-class="animated fadeOutRight"
      >
        <div
          v-for="criteria in criterions"
          :id="'criteria_' + criteria.id"
          :key="criteria.id"
        >
          <rubric-criteria
            :criteria="criteria"
            @input="criteria = $event"
            @remove="removeCriteria(criteria.id)"
          >
          </rubric-criteria>
        </div>
      </transition-group>

      <div class="columns col-12">
        <div v-if="criterions.length > 0" class="column col-4 col-ml-auto pt-2">
          <button class="btn btn-block float-right" @click="addCriteria()">
            Add New Criteria
          </button>
        </div>
      </div>

      <div class="columns col-12 pt-2">
        <div class="column col-2">
          <h5 class="pt-2">
            Total Points: <span>{{ totalPoints }}</span>
          </h5>
        </div>
        <div class="column col-2 col-ml-auto">
          <button
            class="btn btn-primary float-right"
            data-test="create-rubric"
            @click="createRubric()"
          >
            Create Rubric
          </button>
        </div>
      </div>
    </div>

    <div
      v-if="!rubricsLoading"
      id="rubricSelector"
      class="modal"
      :class="{ active: showRubricList }"
    >
      <a
        class="modal-overlay"
        aria-label="Close"
        @click="showRubricList = !showRubricList"
      ></a>
      <div class="modal-container">
        <div class="modal-header">
          <a
            class="btn btn-clear float-right"
            aria-label="Close"
            @click="showRubricList = !showRubricList"
          ></a>
          <div class="modal-title h5">Select Rubric to Clone</div>
        </div>
        <div class="modal-body">
          <div class="content">
            <!-- content here -->
            <div v-if="!rubrics.length" class="toast toast-error">
              There are no rubrics to copy the content from.
            </div>

            <div class="form-group">
              <label
                v-for="rubric in rubrics"
                :key="rubric.name"
                class="form-radio"
              >
                <input v-model="chosenRubric" type="radio" :value="rubric.id" />
                <i class="form-icon"></i> {{ rubric.name }} <br />
                <small class="text-gray-dark">{{ rubric.description }}</small>
              </label>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button
            class="btn btn-primary"
            :disabled="!chosenRubric"
            @click="cloneRubric()"
          >
            Clone
          </button>
        </div>
      </div>
    </div>

    <div class="modal modal-sm" :class="{ active: fetchingCriterions }">
      <a class="modal-overlay"></a>
      <div class="modal-container">
        <div class="modal-header">Cloning content ...</div>
        <div class="modal-body"><div class="loading"></div></div>
      </div>
    </div>
  </main>
</template>

<script>
import RubricCriteria from "../components/rubric/RubricCriteria"
import { mapActions, mapState, mapGetters } from "vuex"
import Octicon from "vue-octicon/components/Octicon"
import "vue-octicon/icons/question"

export default {
  name: "RubricCreator",
  components: {
    RubricCriteria,
    Octicon
  },
  data: function() {
    return {
      rubric_name: "",
      makePublic: true,
      criterions: [],
      criteriaCounter: 0,
      description: "",
      showRubricList: false,
      rubricsFetched: false,
      chosenRubric: 0,
      fetchingCriterions: false
    }
  },
  computed: {
    ...mapState({
      rubrics: state => state.rubric.all,
      rubricsLoading: state => state.rubric.isLoading
    }),
    ...mapGetters("rubric", ["totalPoints"]),
    totalPoints: function() {
      return this.criterions
        .map(criteria =>
          Math.max(...criteria.levels.map(l => parseFloat(l.points)))
        )
        .reduce((a, b) => a + b, 0)
    }
  },
  created() {
    this.$store.dispatch("rubric/getAllRubrics")
  },
  methods: {
    ...mapActions("rubric", ["createNewRubric", "getRubricWithCriterions"]),
    cloneRubric: function() {
      const self = this
      self.showRubricList = false
      self.fetchingCriterions = true
      self
        .getRubricWithCriterions(self.chosenRubric)
        .then(rubric => {
          self.criterions = rubric.criterions
          self.fetchingCriterions = false
          self.$nextTick(() => self.$refs.rname.focus())
        })
        .catch(error => {
          self.fetchingCriterions = false
          self.$toasted.error(
            "Failed to clone the rubric. " + error.statusText,
            {
              duration: 3000
            }
          )
        })
    },
    addCriteria: function() {
      let criteriaID = this.criteriaCounter
      this.criteriaCounter++

      let criteria = {
        id: criteriaID,
        name: "Criteria " + (criteriaID + 1),
        levels: []
      }
      this.criterions.push(criteria)
    },
    createRubric: function() {
      const self = this
      if (self.rubric_name.trim().length === 0) {
        self.$toasted.error("Rubric name cannot be empty", { duration: 3000 })
        return
      }
      let rubric = {
        name: self.rubric_name,
        public: self.makePublic,
        description: self.description,
        criterions: self.criterions
      }
      self.createNewRubric(rubric).then(() => {
        self.$toasted.success(
          "Rubric Created successfully. Redirecting you back ...",
          { duration: 5000 }
        )
        setTimeout(() => self.$router.go(-1), 5000)
      })
    },
    removeCriteria: function(id) {
      let remove = confirm(
        "Do you want to remove this criteria from the rubric?"
      )
      if (!remove) {
        return
      }
      let index = this.criterions.indexOf(c => c.id === id)
      this.criterions.splice(index, 1)
    }
  }
}
</script>

<style scoped></style>
