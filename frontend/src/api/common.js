export const authHead = function(token) {
  return {
    headers: { Authorization: "Bearer ".concat(token) }
  }
}
