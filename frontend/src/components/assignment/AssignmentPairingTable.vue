<template>
  <section>
    <div v-if="!isLoading && !pairings.length" class="column col-12">
      <empty-state
        title="No Pairs"
        message="No pairs have been created for this assignment"
        action="Create Pairs"
        @empty-action="
          $router.push({ name: 'assignment.pair', params: $route.params })
        "
      >
      </empty-state>
    </div>

    <div v-if="pairings.length" class="panel">
      <div class="panel-body no-padding">
        <table id="pairing-table" class="table table-striped">
          <thead>
            <tr>
              <th style="max-width: 3rem;">#</th>
              <th>
                <div class="columns">
                  <div v-if="!showGraderSearch" class="column col-10 col-sm-11">
                    <label class="form-label">
                      Grader
                      <span
                        class="notify-bell tooltip tooltip-right c-hand ml-2"
                        data-tooltip="Remind everyone with pending reviews"
                        @click="notifyAll()"
                      >
                        <octicon class="icon text-gray" name="bell" />
                      </span>
                    </label>
                  </div>
                  <div v-else class="column col-10 col-sm-11">
                    <input
                      ref="graderInput"
                      v-model.trim="graderFilter"
                      title="Search Graders"
                      type="text"
                      class="form-input input-sm"
                      placeholder="Grader"
                      @change="search()"
                    />
                  </div>
                  <div class="column col-2 col-sm-1">
                    <div class="btn btn-link" @click="toggleSearch('grader')">
                      <octicon
                        v-if="showGraderSearch"
                        name="x"
                        class="icon text-error"
                      />
                      <octicon v-else name="search" class="icon" />
                    </div>
                  </div>
                </div>
              </th>
              <th>
                <div class="columns pl-2">
                  <div v-if="!showRecipSearch" class="column col-10 col-sm-11">
                    <label class="form-label">Recipients</label>
                  </div>
                  <div v-else class="column col-10 col-sm-11">
                    <input
                      ref="recipientInput"
                      v-model.trim="recipientFilter"
                      title="Search Recipients"
                      type="text"
                      class="form-input input-sm"
                      placeholder="Recipients"
                      @change="search()"
                    />
                  </div>
                  <div class="column col-2 col-sm-1">
                    <div
                      class="btn btn-link"
                      @click="toggleSearch('recipient')"
                    >
                      <octicon
                        v-if="showRecipSearch"
                        name="x"
                        class="icon text-error"
                      />
                      <octicon v-else name="search" class="icon" />
                    </div>
                  </div>
                </div>
              </th>
            </tr>
          </thead>
          <tbody v-if="isLoading || searching">
            <tr
              v-for="r in 5"
              :id="'placeholder_row_' + r"
              :key="'dummy_row' + r"
            >
              <td
                v-for="c in 2"
                :id="'cell_r' + r + 'c' + c"
                :key="'dummy_r' + r + '_c' + c"
              >
                <content-placeholders>
                  <content-placeholders-text :lines="1" />
                </content-placeholders>
              </td>
            </tr>
          </tbody>
          <tbody v-else>
            <tr v-if="showSearchResults && !rows().length">
              <td colspan="3" class="text-center">
                <octicon name="alert" class="icon text-warning" /> No pairs
                found!
              </td>
            </tr>
            <tr v-for="(row, index) in rows()" :key="'row' + index">
              <td>
                {{
                  showSearchResults
                    ? index + 1
                    : (pageIndex - 1) * perPage + index + 1
                }}
              </td>
              <td>
                <router-link
                  :to="{
                    name: 'give-feedback',
                    params: { course_id, assignment_id, user_id: row.grader.id }
                  }"
                >
                  {{ row.grader.real_name }}
                </router-link>
                <button
                  class="btn btn-sm btn-link notify-bell tooltip"
                  data-tooltip="Send reminder to complete pending reviews"
                  @click="notifyGrader(row.grader.id)"
                >
                  <octicon class="text-gray" name="bell" />
                </button>
              </td>
              <td>
                <span
                  v-for="pair in row.pairing"
                  :key="'row' + index + '_' + pair.id"
                  class="chip ml-1"
                  :class="{
                    tooltip: pair.recipient.name !== pair.recipient.real_name
                  }"
                  :data-tooltip="pair.recipient.name"
                >
                  <span
                    v-if="pair.task.status === 'COMPLETE'"
                    class="avatar avatar-sm"
                    style="background-color: #dbf9dd; font-size: 0.8rem;"
                  >
                    <i class="icon icon-check text-success ml-1" />
                  </span>
                  <router-link
                    :to="{
                      name: 'give-feedback',
                      params: {
                        course_id,
                        assignment_id,
                        user_id: pair.recipient.id
                      }
                    }"
                  >
                    {{ pair.recipient.real_name }}
                  </router-link>
                  <span
                    class="pl-1 ml-1 delete text-gray"
                    @click="confirmArchivePairing(pair.id)"
                  >
                    <i class="icon icon-cross"></i>
                  </span>
                </span>
              </td>
            </tr>
          </tbody>
          <TableFooter
            v-if="!showSearchResults"
            :page-count="pageCount"
            :per-page="perPage"
            @change-page-size="changePageSize"
            @goto-page="gotoPage"
          />
        </table>
      </div>
    </div>

    <confirm-modal
      title="Are you sure you want to archive this pairing?"
      confirm="Archive Pairing"
      reject="Don't Archive"
      :show-modal="showArchiveConfirmation"
      @rejected="showArchiveConfirmation = false"
      @confirmed="archivePairing()"
    >
      Archiving this pairing will also archive the task associated with it. If
      the student has already submitted a feedback, then the feedback would be
      archived too.
    </confirm-modal>
  </section>
</template>

<script>
import Octicon from "vue-octicon/components/Octicon"
import EmptyState from "../ui/EmptyState"
import ConfirmModal from "../ui/ConfirmModal"
import { mapState } from "vuex"
import "vue-octicon/icons/search"
import "vue-octicon/icons/x"
import "vue-octicon/icons/alert"
import "vue-octicon/icons/bell"
import notificationAPI from "../../api/notification"
import TableFooter from "../ui/TableFooter"

export default {
  name: "AssignmentPairingTable",
  components: {
    TableFooter,
    ConfirmModal,
    Octicon,
    EmptyState
  },
  data: function() {
    return {
      course_id: 0,
      assignment_id: 0,
      graderFilter: "",
      recipientFilter: "",
      pageIndex: 1,
      perPage: 10,
      jumpPageNumber: 1,
      showRecipSearch: false,
      showGraderSearch: false,
      showSearchResults: false,
      toArchive: 0,
      showArchiveConfirmation: false
    }
  },
  computed: {
    ...mapState({
      pairings: state => state.pairing.all,
      isLoading: state => state.pairing.isLoading,
      results: state => state.pairing.searchResults,
      searching: state => state.pairing.searching,
      pageCount: state => state.pairing.pageCount
    })
  },
  watch: {
    pageIndex: function() {
      this.getPairs()
    },
    perPage: function() {
      if (this.pageIndex !== 1) {
        // this will automatically get the pairs due to the watcher
        this.pageIndex = 1
      } else {
        // if it is already in the first page, then reload using new values
        this.getPairs()
      }
    }
  },
  created() {
    this.course_id = parseInt(this.$route.params.course_id)
    this.assignment_id = parseInt(this.$route.params.assignment_id)
    this.getPairs()
  },
  methods: {
    gotoPage: function(page) {
      if (Number.isInteger(page)) this.pageIndex = page
    },
    changePageSize: function(size) {
      this.perPage = size
    },
    rows: function() {
      return this.showSearchResults ? this.results : this.pairings
    },
    toggleSearch: function(userType) {
      if (userType === "grader") {
        this.showGraderSearch = !this.showGraderSearch
        if (this.showGraderSearch) {
          this.$nextTick(() => this.$refs.graderInput.focus())
        } else {
          this.graderFilter = ""
          this.search()
        }
      } else if (userType === "recipient") {
        this.showRecipSearch = !this.showRecipSearch
        if (this.showRecipSearch) {
          this.$nextTick(() => this.$refs.recipientInput.focus())
        } else {
          this.recipientFilter = ""
          this.search()
        }
      }

      if (!this.showGraderSearch && !this.showRecipSearch) {
        this.showSearchResults = false
        this.getPairs()
      }
    },
    search: function() {
      if (!this.recipientFilter.length && !this.graderFilter.length) return

      let data = { ...this.$route.params }
      if (this.graderFilter.length) {
        data.grader = this.graderFilter
      }
      if (this.recipientFilter.length) {
        data.recipient = this.recipientFilter
      }
      this.$store.dispatch("pairing/searchPairings", data)
      this.showSearchResults = true
    },
    getPairs: function() {
      if (this.showSearchResults) return
      this.$store.dispatch("pairing/getPairingPage", {
        course_id: this.course_id,
        assignment_id: this.assignment_id,
        page: this.pageIndex,
        per_page: this.perPage
      })
    },
    confirmArchivePairing: function(pairing_id) {
      this.toArchive = pairing_id
      this.showArchiveConfirmation = true
    },
    archivePairing: function() {
      this.$store.dispatch("pairing/archive", this.toArchive)
      this.toArchive = 0
      this.showArchiveConfirmation = false
    },
    notifyAll: function() {
      notificationAPI
        .sendPendingReminder(this.course_id, this.assignment_id)
        .then(() => {
          this.$toasted.success(
            "Reminder emails will be dispatched to all students with pending reviews",
            { duration: 3000 }
          )
        })
        .catch(err => {
          let msg = "Reminder emails couldn't be sent."
          if (err.hasOwnProperty("response")) {
            msg += " " + err.response.statusText
          }
          this.$toasted.error(msg, { duration: 3000 })
        })
    },
    notifyGrader: function(grader) {
      notificationAPI
        .sendPendingReminder(this.course_id, this.assignment_id, grader)
        .then(() => {
          this.$toasted.success("Reminder email sent", { duration: 3000 })
        })
        .catch(err => {
          let msg = "Reminder emails couldn't be sent."
          if (err.hasOwnProperty("response")) {
            msg += " " + err.response.statusText
          }
          this.$toasted.error(msg, { duration: 3000 })
        })
    }
  }
}
</script>

<style scoped>
.no-padding {
  padding: 0;
  overflow: visible;
}
.table {
  font-size: 0.7rem;
}
.chip:hover {
  background-color: #e2e3e6;
}
.chip a:hover {
  text-decoration: none;
}
.chip > .delete:hover {
  color: #cc0000 !important;
}
.notify-bell:hover > .octicon {
  color: #ffb700 !important;
}
</style>
