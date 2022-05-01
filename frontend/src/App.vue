<template>
  <div id="app" class="container grid-lg">
    <top-nav></top-nav>
    <div
      v-if="!isLoggedIn && hasRefreshToken"
      class="centered text-center page"
      style="padding-top: 35vh;"
    >
      <div class="loading loading-lg"></div>
      <p class="mt-2">Logging you in ...</p>
    </div>
    <router-view></router-view>

    <page-footer></page-footer>
  </div>
</template>

<script>
import TopNav from "./components/TopNav"
import PageFooter from "./components/PageFooter"

import { mapGetters, mapState } from "vuex"

export default {
  name: "App",
  components: {
    TopNav,
    PageFooter
  },
  computed: {
    ...mapGetters("user", ["isLoggedIn", "hasRefreshToken"]),
    ...mapState({
      messages: state => state.logger.all
    })
  },
  watch: {
    messages: function(msgs) {
      if (!msgs.length) return
      let latest = msgs[msgs.length - 1]
      this.$toasted.show(latest.message, { duration: 3000, type: latest.level })
    }
  },
  created() {
    // A Hack to show a different favicon whenever the application is run in development mode
    if (process.env.NODE_ENV === "development") {
      let links = document.getElementsByTagName("link")
      for (let i = 0; i < links.length; i++) {
        if (links[i].getAttribute("sizes") === "16x16") {
          links[i].setAttribute("href", "/app/img/icons/favicon-dev-16x16.png")
        } else if (links[i].getAttribute("sizes") === "32x32") {
          links[i].setAttribute("href", "/app/img/icons/favicon-dev-32x32.png")
        }
      }
    }
  }
}
</script>

<style lang="scss">
$warning-text-color: #755a00;
@import "node_modules/spectre.css/src/spectre";
@import "node_modules/spectre.css/src/icons";
@import "node_modules/spectre.css/src/spectre-exp";
@import "node_modules/animate.css/animate";

h1,
.h1 {
  font-size: 1.5rem;
}

h2,
.h2 {
  font-size: 1rem;
  text-transform: uppercase;
  font-weight: 300;
  letter-spacing: 0.1rem;
}

h3,
.h3 {
  font-size: 0.9rem;
}

p {
  margin: 0 0 0.5rem;
}

.toast.toast-warning {
  color: $warning-text-color;
}

.page {
  min-height: calc(100vh - 8rem);
}

.menu {
  -webkit-box-shadow: none;
  box-shadow: none;
  border: 1px solid #f0f1f4;
}

@keyframes fadeoutBg {
  0% {
    background-color: #f1f1fc;
  }
  100% {
    background-color: #fff;
  }
}
.highlight {
  animation: fadeoutBg 10s linear;
}
</style>
