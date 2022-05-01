<template>
  <div class="panel">
    <div class="panel-nav mx-2 px-2">
      <ul class="tab">
        <li
          class="tab-item"
          :class="{ active: currentTab === 'write' }"
          @click="currentTab = 'write'"
        >
          <a>Write</a>
        </li>
        <li
          class="tab-item"
          :class="{ active: currentTab === 'preview' }"
          @click="currentTab = 'preview'"
        >
          <a>Preview</a>
        </li>
        <li class="tab-item tab-action">
          <div class="input-group input-inline text-gray editor-icon-holder">
            <div
              v-shortkey="['ctrl', 'alt', 'b']"
              class="editor-icon tooltip"
              data-tooltip="Bold - Ctrl+Alt+B"
              @click="insert('bold')"
              @shortkey="insert('bold')"
            >
              <octicon name="bold" class="icon"></octicon>
            </div>
            <div
              v-shortkey="['ctrl', 'alt', 'i']"
              class="editor-icon tooltip"
              data-tooltip="Italic - Ctrl+Alt+I"
              @click="insert('italic')"
              @shortkey="insert('italic')"
            >
              <octicon name="italic" class="icon"></octicon>
            </div>
            <div
              v-shortkey="['ctrl', 'alt', 'r']"
              class="editor-icon tooltip"
              data-tooltip="Quote - Ctrl+Alt+R"
              @click="insert('quote')"
              @shortkey="insert('quote')"
            >
              <octicon name="quote" class="icon"></octicon>
            </div>
            <div
              v-shortkey="['ctrl', 'alt', 'c']"
              class="editor-icon tooltip"
              data-tooltip="Code - Ctrl+Alt+C"
              @click="insert('code')"
              @shortkey="insert('code')"
            >
              <octicon name="code" class="icon"></octicon>
            </div>
            <div
              v-shortkey="['ctrl', 'alt', 'l']"
              class="editor-icon tooltip"
              data-tooltip="Link - Ctrl+Alt+L"
              @click="insert('link')"
              @shortkey="insert('link')"
            >
              <octicon name="link" class="icon"></octicon>
            </div>
            <div
              v-shortkey="['ctrl', 'alt', 'u']"
              class="editor-icon tooltip"
              data-tooltip="Bullet list - Ctrl+Alt+U"
              @click="insert('ul')"
              @shortkey="insert('ul')"
            >
              <octicon name="list-unordered" class="icon"></octicon>
            </div>
            <div
              v-shortkey="['ctrl', 'alt', 'n']"
              class="editor-icon tooltip tooltip-left"
              data-tooltip="Numbered list - Ctrl+Alt+N"
              @click="insert('ol')"
              @shortkey="insert('ol')"
            >
              <octicon name="list-ordered" class="icon"></octicon>
            </div>
            <emoji-picker :search="emojiSearch" @emoji="insert">
              <div
                slot="emoji-invoker"
                slot-scope="{
                  events: { click: clickEvent }
                }"
                class="editor-icon tooltip"
                data-tooltip="Emoji"
                @click.stop="clickEvent"
              >
                <octicon name="smiley" class="icon"></octicon>
              </div>
              <div
                slot="emoji-picker"
                slot-scope="{
                  emojis,
                  insert,
                  // eslint-disable-next-line
                  display
                }"
                class="emoji-tray card"
              >
                <div class="form-group has-icon-right">
                  <input
                    v-model="emojiSearch"
                    type="text"
                    class="form-input input-sm"
                  />
                  <i class="form-icon icon icon-search"></i>
                </div>
                <div>
                  <div>
                    <div
                      v-for="(emojiGroup, category) in emojis"
                      :key="category"
                    >
                      <h5>{{ category }}</h5>
                      <div>
                        <span
                          v-for="(emoji, emojiName) in emojiGroup"
                          :key="emojiName"
                          :title="emojiName"
                          @click="insert(emoji)"
                        >
                          {{ emoji }}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </emoji-picker>
          </div>
        </li>
      </ul>
    </div>

    <div class="panel-body editor-body">
      <span>
        {{feedbackSuggestion}}
      </span>
      <div v-if="currentTab === 'write'">
        <textarea
          ref="editor"
          v-model="content"
          class="form-input editor-input"
          placeholder="Your feedback"
          @input="$emit('input', content)"
          @blur="emitOnBlur()"
        ></textarea>
      </div>
      <div
        v-if="currentTab === 'preview'"
        class="py-2 editor-input"
        v-html="m2html(content)"
      ></div>

      <div class="py-1 text-gray">
        <small>
          <a href="https://www.markdownguide.org/basic-syntax" target="_blank">
            Markdown
          </a>
          is supported
        </small>
      </div>
    </div>
  </div>
</template>

<script>
import Octicon from "vue-octicon/components/Octicon.vue"
import "vue-octicon/icons/bold"
import "vue-octicon/icons/italic"
import "vue-octicon/icons/quote"
import "vue-octicon/icons/link"
import "vue-octicon/icons/code"
import "vue-octicon/icons/list-ordered"
import "vue-octicon/icons/list-unordered"
import "vue-octicon/icons/smiley"
import marked from "marked"
import EmojiPicker from "vue-emoji-picker"

export default {
  name: "MarkdownEditor",
  components: {
    Octicon,
    EmojiPicker
  },
  props: {
    initialText: {
      type: String,
      default: ""
    },
    feedbackSuggestion: {
      type: String,
      default: ""
    }
  },
  data: function() {
    return {
      currentTab: "write",
      content: "",
      emojiSearch: ""
    }
  },
  mounted() {
    this.content = this.initialText || ""
    this.$emit("input", this.content)
  },
  methods: {
    m2html: function(value) {
      return marked(value)
    },
    emitOnBlur: function() {
      const self = this
      setTimeout(() => self.$emit("save-draft"), 500)
    },
    insert: function(marker) {
      let tArea = this.$refs.editor
      let startPos = tArea.selectionStart,
        endPos = tArea.selectionEnd,
        cursorPos = startPos,
        tmpStr = tArea.value,
        selection = tArea.value.substring(startPos, endPos)

      let positions = 0
      let formatter = ""
      let converted_lines = ""
      let i = 1

      switch (marker) {
        case "bold":
          formatter = "**" + selection + "**"
          positions = 2 + selection.length
          break
        case "italic":
          formatter = "*" + selection + "*"
          positions = 1 + selection.length
          break
        case "quote":
          formatter = "\n\n> " + selection + "\n"
          positions = 4 + selection.length
          break
        case "code":
          formatter = "\n```\n" + selection + "\n```"
          positions = 5 + selection.length
          break
        case "link":
          formatter = "[" + selection + "]()"
          positions = 1 + selection.length
          break
        case "ul":
          converted_lines = selection.replace(/\n/g, "\n* ")
          formatter = "* " + converted_lines
          positions = formatter.length
          break
        case "ol":
          converted_lines = selection.replace(/\n/g, () => `\n${++i}. `)
          formatter = "1. " + converted_lines
          positions = formatter.length
          break
        default:
          // emojis
          formatter = marker
          positions = marker.length
      }
      this.content =
        tmpStr.substring(0, startPos) +
        formatter +
        tmpStr.substring(endPos, tmpStr.length)
      console.log(this.content)
      this.$emit("input", this.content)
      setTimeout(() => {
        tArea.focus()
        tArea.selectionStart = tArea.selectionEnd = cursorPos + positions
      }, 20)
    }
  }
}
</script>

<style scoped>
.editor-icon-holder {
  position: relative;
}
.editor-icon {
  width: 1.5rem;
}
.editor-icon:hover {
  color: #5755d9;
}
.editor-input {
  min-width: 100%;
  max-width: 100%;
  border: 0;
  resize: vertical;
  min-height: 10rem;
  margin: 3px auto;
  z-index: 1;
}
.editor-body {
  min-height: 10rem;
}

.tab-item {
  cursor: pointer;
}
.emoji-tray {
  height: 300px;
  width: 250px;
  max-width: 250px;
  overflow-x: hidden;
  overflow-y: scroll;
  z-index: 9;
  position: absolute;
  right: 0;
  padding: 5px;
}
.emoji-tray h5 {
  font-size: 0.7rem;
  margin-top: 0.5rem;
  margin-bottom: 0.5rem;
  border-bottom: 1px solid #efeff4;
}
.emoji-tray .form-input {
  width: 100%;
}
</style>
