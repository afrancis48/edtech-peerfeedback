<template>
  <main>
    <div class="columns">
      <div class="column col-8"><h2>Your Rubrics</h2></div>
      <div class="column col-4">
        <router-link
          :to="{ name: 'rubric-creator' }"
          class="btn btn-default float-right"
        >
          New Rubric
        </router-link>
      </div>

      <div v-if="!rubricsLoading && !all.length" class="column col-12">
        <empty-state
          title="No Rubrics"
          message="You have not created any Rubrics."
          action="Create a rubric"
          @empty-action="$router.push({ name: 'rubric-creator' })"
        >
        </empty-state>
      </div>

      <div v-else class="column col-12">
        <table class="table table-striped">
          <thead>
            <tr>
              <th>Rubric</th>
              <th>Public</th>
              <th>Active</th>
            </tr>
          </thead>
          <tbody v-if="rubricsLoading">
            <tr v-for="i in 3" :key="'cpRow' + i">
              <td v-for="j in 4" :key="'cpCellR' + i + 'C' + j">
                <content-placeholders>
                  <content-placeholders-text :lines="1" />
                </content-placeholders>
              </td>
            </tr>
          </tbody>
          <tbody v-else>
            <tr v-for="rubric in all" :key="rubric.id">
              <td>
                <h6>
                  <a :href="'#' + rubric.id" @click="showRubric(rubric.id)">
                    {{ rubric.name }}
                  </a>
                </h6>
                <p>{{ rubric.description }}</p>
              </td>
              <td>
                <div class="form-group">
                  <label class="form-switch">
                    <input
                      type="checkbox"
                      :checked="rubric.public"
                      @change="togglePublic(rubric)"
                    />
                    <i class="form-icon"></i>
                  </label>
                </div>
              </td>
              <td>
                <div class="form-group">
                  <label class="form-switch">
                    <input
                      type="checkbox"
                      :checked="rubric.active"
                      :disabled="rubric.in_use"
                      @change="toggleActive(rubric)"
                    />
                    <i class="form-icon"></i>
                    <span
                      v-if="rubric.in_use"
                      class="text-gray tooltip"
                      data-tooltip="Rubric in use. Cannot deactivate."
                    >
                      <octicon name="question" class="icon"></octicon>
                    </span>
                  </label>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Rubric Viewer Modal -->
    <Modal
      :show-modal="showRubricModal"
      size="large"
      @modalClosed="showRubricModal = false"
    >
      <table v-if="isLoading">
        <tr v-for="i in 3" :key="'cpRow' + i">
          <td v-for="j in 4" :key="'cpCellR' + i + 'C' + j">
            <content-placeholders>
              <content-placeholders-text :lines="1" />
            </content-placeholders>
          </td>
        </tr>
      </table>

      <RubricViewer v-else :rubric="current" />
    </Modal>
  </main>
</template>

<script>
import { mapState, mapActions } from "vuex"
import EmptyState from "../components/ui/EmptyState"
import Modal from "../components/ui/Modal"
import RubricViewer from "../components/rubric/RubricViewer"
import Octicon from "vue-octicon/components/Octicon"
import "vue-octicon/icons/question"

export default {
  name: "RubricManager",
  components: {
    EmptyState,
    Modal,
    RubricViewer,
    Octicon
  },
  data: function() {
    return {
      showRubricModal: false
    }
  },
  computed: {
    ...mapState("rubric", ["rubricsLoading", "all", "isLoading", "current"])
  },
  created() {
    this.$store.dispatch("rubric/loadMyRubrics")
  },
  methods: {
    ...mapActions("rubric", ["togglePublic", "toggleActive"]),
    showRubric: function(rubric_id) {
      this.$store.dispatch("rubric/setCurrent", rubric_id)
      this.showRubricModal = true
    }
  }
}
</script>

<style scoped></style>
