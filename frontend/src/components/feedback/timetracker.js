/*
    A Mixin for tracking the time spend on the components
 */

export const TimeTracker = {
  data: function() {
    return {
      startStopTimes: {},
      idleTimeoutMs: 30 * 1000,
      currentIdleTimeMs: 0,
      checkInterval: 500,
      active: false,
      idle: false,
      timeFlags: [],
      emitInterval: 5000,
      tEmitMessage: "elapsed-time",
      emitElapsedTime: false
    }
  },
  methods: {
    startListening: function() {
      let hiddenProp = "hidden"
      let visibilityEvent = "visibilitychange"

      if (typeof document.mozHidden !== "undefined") {
        hiddenProp = "mozHidden"
        visibilityEvent = "mozvisibilitychange"
      } else if (typeof document.msHidden !== "undefined") {
        hiddenProp = "msHidden"
        visibilityEvent = "msvisibiiltychange"
      } else if (typeof document.webkitHidden !== "undefined") {
        hiddenProp = "webkitHidden"
        visibilityEvent = "webkitvisibilitychange"
      }

      const self = this
      window.addEventListener("blur", () => self.stopTimer())
      window.addEventListener("focus", () => self.resetIdleCountdown())
      window.addEventListener("scroll", () => self.resetIdleCountdown())
      document.addEventListener(
        visibilityEvent,
        function() {
          if (document[hiddenProp]) {
            self.stopTimer()
          } else {
            self.startTimer()
          }
        },
        false
      )
      document.addEventListener("mousemove", () => self.resetIdleCountdown())
      document.addEventListener("keyup", () => self.resetIdleCountdown())
      document.addEventListener("touchstart", () => self.resetIdleCountdown())

      this.$el.addEventListener("mouseover", () => self.startTimer())
      this.$el.addEventListener("mousemove", () => self.startTimer())
      this.$el.addEventListener("mouseleave", () => self.stopTimer())
      this.$el.addEventListener("keypress", () => self.startTimer())
      this.$el.addEventListener("focus", () => self.startTimer())

      setInterval(() => self.checkState(), self.checkInterval)
      setInterval(() => self.emitElapsed(), self.emitInterval)
    },
    resetIdleCountdown: function() {
      this.idle = false
      this.currentIdleTimeMs = 0
    },
    checkState: function() {
      if (this.idle === false && this.currentIdleTimeMs > this.idleTimeoutMs) {
        this.idle = true
        this.stopTimer()
      } else {
        this.currentIdleTimeMs += this.checkInterval
      }
    },
    stopTimer: function() {
      if (!this.timeFlags.length) return
      if (
        typeof this.timeFlags[this.timeFlags.length - 1].stopTime ===
        "undefined"
      ) {
        this.timeFlags[this.timeFlags.length - 1].stopTime = new Date()
      }
      this.active = false
    },
    startTimer: function() {
      // start the timer only when the most recent flag has a stop time or there
      // are no flags
      if (
        !this.timeFlags.length ||
        typeof this.timeFlags[this.timeFlags.length - 1].stopTime !==
          "undefined"
      ) {
        this.timeFlags.push({ startTime: new Date() })
      }
      this.active = true
    },
    getElapsedTime: function() {
      let elapsed = this.timeFlags.reduce((acc, val) => {
        let stopTime =
          typeof val.stopTime === "undefined" ? new Date() : val.stopTime
        let diff = Number(stopTime - val.startTime)
        return acc + diff
      }, 0)
      return elapsed / 1000
    },
    emitElapsed: function() {
      if (!this.emitElapsedTime) return
      this.$emit(this.tEmitMessage, this.getElapsedTime())
    }
  },
  mounted: function() {
    if (typeof this.enableTimer === "boolean" && !this.enableTimer) return
    this.startListening()
  }
}
