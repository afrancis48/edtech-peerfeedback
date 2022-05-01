<template>
  <div :id="id" class="pdf">
    <object :data="pdfUrl(file)" type="application/pdf" width="100%">
      <iframe
        :src="pdfUrl(file)"
        width="100%"
        height="100%"
        style="height: 100vh;"
      >
        This browser does not support PDFs. Please download the PDF to view it :
        <a :href="file">Download PDF</a>.
      </iframe>
    </object>
  </div>
</template>

<script>
export default {
  props: {
    file: {
      type: String,
      required: true
    },
    id: {
      type: String,
      required: true
    }
  },
  methods: {
    pdfUrl: function(file) {
      return "/api/pdf/?url=" + encodeURIComponent(file)
    }
  }
}
</script>

<style scoped>
.pdf object {
  height: 100vh;
}
</style>
