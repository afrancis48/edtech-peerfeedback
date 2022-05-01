module.exports = {
  devServer: {
    port: 4000,
    allowedHosts: [".gatech.edu", ".peerfeedback.io", "localhost"],
    proxy: {
      "/api": {
        target: "http://localhost:5000/"
      },
      "/users": {
        target: "http://localhost:5000/",
        changeOrigin: false
      }
    }
  },

  outputDir: "../peerfeedback/static/",

  pluginOptions: {
    webpackBundleAnalyzer: {
      openAnalyzer: false
    }
  },

  publicPath: "/app/",
  assetsDir: undefined,
  runtimeCompiler: undefined,
  productionSourceMap: undefined,
  parallel: undefined,
  css: undefined,

  pwa: {
    name: "Peer Feedback",
    themeColor: "#5755d9",
    msTileColor: "#5755d9"
  },

  lintOnSave: true
}
