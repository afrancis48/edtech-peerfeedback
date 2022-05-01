import Vue from "vue"
import Router from "vue-router"
import store from "./store"

Vue.use(Router)

const router = new Router({
  mode: "history",
  base: "/app/",
  routes: [
    {
      name: "dashboard",
      path: "/dashboard",
      component: () =>
        import(/* webpackChunkName: "dashboard" */ "./views/Dashboard.vue"),
      meta: { desc: "Dashboard", requiresAuth: true },
      alias: "/"
    },
    {
      name: "course",
      path: "/course/:id/",
      component: () =>
        import(/* webpackChunkName: "course" */ "./views/Course.vue"),
      meta: { desc: "Course View", requiresAuth: true },
      children: [
        {
          name: "course-wide-settings",
          path: "course-wide-settings",
          component: () =>
            import(/* webpackChunkName: "course-settings" */ "./components/course/CourseSettings"),
          meta: { desc: "Course-wide Settings", requiresAuth: true }
        }
      ]
    },
    {
      name: "assignment",
      path: "/course/:course_id/assignment/:assignment_id/",
      component: () =>
        import(/* webpackChunkName: "assignment" */ "./views/Assignment.vue"),
      meta: { desc: "Assignment View", requiresAuth: true },
      children: [
        {
          name: "assignment.settings",
          path: "settings",
          component: () =>
            import(/* webpackChunkName: "assign-settings" */ "./components/assignment/AssignmentSettings")
        },
        {
          name: "assignment.pairing-table",
          path: "pairing-table",
          component: () =>
            import(/* webpackChunkName: "pairing-table" */ "./components/assignment/AssignmentPairingTable")
        },
        {
          name: "assignment.pair",
          path: "pair",
          component: () =>
            import(/* webpackChunkName: "pairing" */ "./components/assignment/AssignmentPairing")
        },
        {
          name: "assignment.rubric",
          path: "rubric",
          component: () =>
            import(/* webpackChunkName: "rubric" */ "./components/assignment/AssignmentRubric")
        },
        {
          name: "assignment.data",
          path: "data",
          component: () =>
            import(/* webpackChunkName: "data" */ "./components/assignment/AssignmentData")
        },
        {
          name: "assignment.metrics",
          path: "metrics",
          component: () =>
            import(/* webpackChunkName: "metrics" */ "./components/assignment/AssignmentTaskMetrics")
        }
      ]
    },
    {
      name: "give-feedback",
      path:
        "/feedback/course/:course_id/assignment/:assignment_id/user/:user_id/view_only/:view_only",
      component: () =>
        import(/* webpackChunkName: "feedback" */ "./views/Feedback.vue"),
      meta: { desc: "Give Feedback", requiresAuth: true }
    },
    {
      name: "user-settings",
      path: "/user/settings/",
      component: () =>
        import(/* webpackChunkName: "user-settings" */ "./views/UserSettings.vue"),
      meta: { desc: "User Settings", requiresAuth: true }
    },
    {
      name: "public-profile",
      path: "/user/:id/profile/",
      component: () =>
        import(/* webpackChunkName: "profile" */ "./views/UserPublicProfile.vue"),
      meta: { desc: "User Profile", requiresAuth: true }
    },
    {
      name: "logout",
      path: "/user/logout/",
      component: () =>
        import(/* webpackChunkName: "logout" */ "./views/LoggedOut.vue"),
      meta: { desc: "Logged Out", requiresAuth: true }
    },
    {
      name: "rubric-creator",
      path: "/rubric/creator",
      component: () =>
        import(/* webpackChunkName: "creator" */ "./views/RubricCreator.vue"),
      meta: { desc: "Rubric Creator", requiresAuth: true }
    },
    {
      name: "rubric-manager",
      path: "/rubric/manager",
      component: () =>
        import(/* webpackChunkName: "manager" */ "./views/RubricManager"),
      meta: { desc: "Rubric Manager", requiresAuth: true }
    },
    {
      name: "my-feedbacks",
      path: "/user/feedback/",
      component: () =>
        import(/* webpackChunkName: "myfbs" */ "./views/MyFeedbacks"),
      meta: { desc: "All Your Feedback", requiresAuth: true }
    },
    {
      name: "data-exporter",
      path: "/course/:id/data-exporter",
      component: () =>
        import(/* webpackChunkName: "exporter" */ "./views/DataExporter"),
      meta: { desc: "Data Exporter", requiresAuth: true }
    },
    {
      name: "privacy-policy",
      path: "/privacy-policy",
      component: () =>
        import(/* webpackChunkName: "exporter" */ "./views/PrivacyPolicy.vue"),
      meta: { desc: "Privacy Policy", requiresAuth: false }
    },
    {
      name: "home",
      path: "/home",
      component: () =>
        import(/* webpackChunkName: "home" */ "./views/Home.vue"),
      meta: { desc: "Home", requiresAuth: false },
      alias: "/"
    },
    {
      name: "terms-of-service",
      path: "/terms-of-service",
      component: () =>
        import(/* webpackChunkName: "exporter" */ "./views/TermsOfService.vue"),
      meta: { desc: "Terms of Service", requiresAuth: false }
    },
    {
      name: "case-study",
      path: "/case-study",
      component: () =>
        import(/* webpackChunkName: "exporter" */ "./views/CaseStudy.vue"),
      meta: { desc: "Case Study", requiresAuth: false }
    },
    {
      name: "all-courses",
      path: "/courses/all/",
      component: () =>
        import(/* webpackChunkName: "allcourses" */ "./views/AllCourses.vue"),
      meta: { desc: "All Courses", requiresAuth: true }
    },
    {
      path: "*",
      component: () =>
        import(/* webpackChunkName: "404" */ "./views/NotFound404.vue"),
      mets: { desc: "404", requiresAuth: false }
    }
  ]
})

router.beforeEach((to, from, next) => {
  if (
    // The route requires auth but the user is not logged in
    to.matched.some(record => record.meta.requiresAuth) &&
    !store.getters["user/isLoggedIn"]
  ) {
    // take user to home page
    next({ name: "home" })
  }
  // all other times, forward to destination
  next()
})

export default router
