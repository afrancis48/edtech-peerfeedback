module.exports = {
  root: true,
  env: {
    node: true
  },
  extends: ["plugin:vue/recommended", "@vue/prettier"],
  rules: {
    "no-console": "off",
    "no-debugger": "off",
    semi: [2, "never"],
    "vue/html-indent": ["error", 2],
    "vue/no-vhtml": "off",
    enforce: "pre",
    test: /\.(js|vue)$/,
    loader: "eslint-loader",
    exclude: /node_modules/
  },
  parserOptions: {
    parser: "babel-eslint"
  },
  plugins: ["vue"]
}
