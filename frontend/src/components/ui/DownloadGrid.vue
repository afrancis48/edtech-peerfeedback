<template>
  <div class="columns">
    <div
      v-for="attachment in submission.attachments"
      :key="attachment.filename"
      class="column col-6 col-md-9 col-xs-12"
    >
      <div class="tile tile-centered pt-2">
        <div class="tile-icon">
          <octicon :name="icon(attachment['content-type'])" scale="3"></octicon>
        </div>
        <div class="tile-content">
          <div class="tile-title">{{ attachment.display_name }}</div>
          <div class="tile-subtitle text-gray">
            <span>
              {{ Math.round(attachment.size / 1000) }} KB ·
              <a :href="attachment.url" class="btn btn-link">
                <octicon name="desktop-download" class="icon"></octicon>
                Download
              </a>
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import Octicon from "vue-octicon/components/Octicon"
import "vue-octicon/icons/file"
import "vue-octicon/icons/file-pdf"
import "vue-octicon/icons/file-media"
import "vue-octicon/icons/device-camera-video"
import "vue-octicon/icons/file-binary"
import "vue-octicon/icons/file-code"
import "vue-octicon/icons/file-zip"
import "vue-octicon/icons/unmute"
import "vue-octicon/icons/desktop-download"

export default {
  name: "DownloadGrid",
  components: {
    Octicon
  },
  props: {
    submission: {
      type: Object,
      required: true
    }
  },
  methods: {
    icon: function(contentType) {
      const filetype = contentType.split("/")[0]
      const fileformat = contentType.split("/")[1]

      const zips = ["tar", "zip", "gzip", "tar+gzip", "x-rar-compressed"]
      const textCode = ["css", "html", "xml"]

      if (filetype === "application") {
        if (fileformat.search("pdf") !== -1) return "file-pdf"
        if (zips.indexOf(fileformat) !== -1) return "file-zip"
      }
      if (filetype === "text" && textCode.indexOf(fileformat) !== -1)
        return "file-code"
      switch (filetype) {
        case "image":
          return "file-media"
        case "audio":
          return "unmute"
        case "video":
          return "device-camera-video"
        case "text":
          return "file"
        default:
          return "file-binary"
      }
    }
  }
}
</script>

<style scoped></style>
