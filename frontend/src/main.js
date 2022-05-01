import Vue from "vue"
import Toasted from "vue-toasted"
import VueContentPlaceholders from "vue-content-placeholders"
import VueScrollTo from "vue-scrollto"
import VueSplit from "vue-split-panel"
import PortalVue from "portal-vue"
import VueFullscreen from "vue-fullscreen"
import VueShortkey from "vue-shortkey"
import * as Sentry from "@sentry/browser"
import * as Integrations from "@sentry/integrations"

import App from "./App.vue"
import store from "./store"
import router from "./router"
import { readableDate, shortDate, shortTime, truncate } from "./utils"

Vue.use(Toasted)
Vue.use(VueContentPlaceholders)
Vue.use(VueScrollTo)
Vue.use(VueSplit)
Vue.use(PortalVue)
Vue.use(VueFullscreen)
Vue.use(VueShortkey)

Vue.filter("readableDate", readableDate)
Vue.filter("shortDate", shortDate)
Vue.filter("shortTime", shortTime)
Vue.filter("truncate", truncate)

Sentry.init({
  dsn: "https://12fd53f256b143cda2a5abebb81cd0e5@sentry.io/1269101",
  integrations: [new Integrations.Vue({ Vue, logErrors: true })]
})

store.dispatch("user/loadTokens").then(() => {
  new Vue({
    store,
    router,
    el: "#app",
    render: h => h(App)
  })
})
