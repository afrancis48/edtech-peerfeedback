<template>
  <main>
    <content-placeholders v-if="profileLoading">
      <content-placeholders-img />
      <content-placeholders-heading />
      <content-placeholders-text />
    </content-placeholders>

    <div v-else class="columns">
      <div class="column col-6">
        <div class="panel">
          <div class="panel-header text-center">
            <avatar :user="profile" size="huge"></avatar>
            <div class="panel-title h5 mt-10">{{ profile.name }}</div>
            <a href="https://gatech.instructure.com/profile/settings">
              Set my profile picture in Canvas
            </a>
          </div>
          <div class="panel-body text-center">
            <p>{{ profile.bio }}</p>
            <reputation
              :feedback-given="profile.feedback_given"
              :user-reputation="profile.reputation"
              :oldest-review="profile.oldest_review"
            />
          </div>
        </div>
      </div>
      <div v-if="!medalsLoading" class="column col-6">
        <div class="panel">
          <div class="panel-header h5">
            Medals
            <span
              class="tooltip tooltip-right c-hand"
              data-tooltip="Explain medals to me"
              @click="showModal = true"
            >
              <octicon name="question" class="text-gray" scale="0.8"></octicon>
            </span>
          </div>
          <div class="panel-body">
            <empty-state
              v-if="!medals.length"
              title="No Medals"
              message="You have not been awarded any medals"
            ></empty-state>
            <div v-for="medal in medals" :key="medal.id" class="medal">
              {{ medal.name }}
            </div>
          </div>
          <div class="panel-footer"></div>
        </div>
      </div>
    </div>

    <modal
      :show-modal="showModal"
      title="Medals"
      @modalClosed="showModal = false"
    >
      <div class="columns">
        <div
          v-for="medal in medalDetails"
          :key="medal.name"
          class="column col-6 col-sm-12 pb-1"
        >
          <div class="card">
            <div class="card-header">
              <div class="medal" :class="'medal-' + medal.category">
                {{ medal.name }}
              </div>
            </div>
            <div class="card-body">{{ medal.description }}</div>
          </div>
        </div>
      </div>
    </modal>
  </main>
</template>

<script>
import { mapState } from "vuex"
import Avatar from "../components/ui/Avatar"
import Modal from "../components/ui/Modal"
import EmptyState from "../components/ui/EmptyState"
import Reputation from "../components/ui/Reputation.vue"
import Octicon from "vue-octicon/components/Octicon"
import "vue-octicon/icons/question"

export default {
  name: "UserPublicProfile",
  components: {
    Avatar,
    Octicon,
    Modal,
    EmptyState,
    Reputation
  },
  data: function() {
    return {
      showModal: false,
      medalDetails: [
        {
          name: "Feedback Master",
          description:
            "Awarded if all the assigned review tasks were completed for a course",
          category: "gold"
        },
        {
          name: "Generous Reviewer",
          description: "Awarded for providing extra feedback 10 or more times",
          category: "silver"
        },
        {
          name: "Super Commentator",
          description: "Awarded if a comment receives 10 hearts or more",
          category: "silver"
        },
        {
          name: "Contributor",
          description: "Awarded after submitting the first review",
          category: "bronze"
        }
      ]
    }
  },
  computed: {
    ...mapState("user", [
      "medalsLoading",
      "profileLoading",
      "medals",
      "profile"
    ])
  },
  created() {
    const user_id = parseInt(this.$route.params.id)
    this.$store.dispatch("user/getProfileOfUser", user_id)
    this.$store.dispatch("user/getMedalsOfUser", user_id)
  }
}
</script>

<style scoped>
.medal:before {
  content: "\01F3C5";
}
.medal {
  border: 1px solid #f1decc;
  padding: 3px 12px;
  display: inline-block;
  border-radius: 0.2rem;
}

.medal-gold:before {
  content: "\01F947";
}
.medal-gold {
  background-color: #f9f5b1;
  border-color: #e1dda1;
}

.medal-silver:before {
  content: "\01F948";
}
.medal-silver {
  border-color: #e0e1e3;
  background-color: #edeeef;
}

.medal-bronze:before {
  content: "\01F949";
}
.medal-bronze {
  border-color: #f1decc;
  background-color: #f9ebe1;
}
</style>
