<template>
  <tfoot>
    <tr>
      <td colspan="3">
        <div class="columns">
          <div class="column col-4 my-1">
            Show
            <div class="input-group input-inline">
              <select
                :value="perPage"
                class="form-select select-sm"
                style="width: 3rem;"
                @change="changePageSize"
              >
                <option value="5">5</option>
                <option value="10">10</option>
                <option value="25">25</option>
                <option value="50">50</option>
                <option value="100">100</option>
              </select>
            </div>
            rows
          </div>

          <div class="column col-2 my-1">
            <div class="input-group input-inline">
              <label for="gotopage" class="pt-1">Go to</label>
              <input
                id="gotopage"
                v-model.number="jumpPageNumber"
                type="number"
                class="form-input input-sm ml-2"
                min="1"
                :max="pageCount"
                @change="jumpToPage()"
              />
            </div>
          </div>

          <div class="column col-6">
            <Pagination
              :per-page="perPage"
              :pages="pageCount"
              :current-page="currentPage"
              @goto="gotoPage"
            />
          </div>
        </div>
      </td>
    </tr>
  </tfoot>
</template>
<script>
import Pagination from "./Pagination"

export default {
  name: "TableFooter",
  components: {
    Pagination
  },
  props: {
    pageCount: {
      type: Number,
      required: true
    },
    perPage: {
      type: Number,
      required: true
    }
  },
  data: function() {
    return {
      jumpPageNumber: 1,
      currentPage: 1
    }
  },
  methods: {
    jumpToPage: function() {
      this.currentPage = this.jumpPageNumber
      this.$emit("goto-page", this.jumpPageNumber)
    },
    gotoPage: function(page) {
      this.jumpPageNumber = page
      this.$emit("goto-page", page)
    },
    changePageSize: function($event) {
      this.$emit("change-page-size", parseInt($event.target.value))
      this.jumpPageNumber = 1
    }
  }
}
</script>
<style scoped>
.pagination {
  margin: 0;
  padding: 0;
}
</style>
