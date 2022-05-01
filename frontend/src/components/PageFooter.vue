<template>
  <section>
    <div class="divider"></div>
    <footer class="footer text-gray text-center">
      <p>
        Designed and built with <span class="text-error">♥</span> for Georgia
        Tech students and faculty.
      </p>
      <p>
        <router-link :to="{ name: 'privacy-policy' }">
          Privacy Policy
        </router-link>
        ·
        <router-link :to="{ name: 'terms-of-service' }">
          Terms of Service
        </router-link>
      </p>
      <p>
        <a href="https://twitter.com/peerfeedbackai">Follow us on Twitter</a> to
        hear about our latest updates!
      </p>
    </footer>
  </section>
</template>

<script>
export default {
  name: "PageFooter"
}
</script>

<style>
.footer {
  padding: 0.5rem 0 1rem 0;
}
</style>
