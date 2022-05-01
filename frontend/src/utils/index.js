/**
 * Function to get the value of Cookie using its name
 *
 * @param {string} cname Name of the Cookie whose value is required
 * @returns {string} The value of the cookie or an empty string if the Cookie is
 *          not found
 */
export const getCookie = function(cname) {
  const name = cname + "="
  const decodedCookie = decodeURIComponent(document.cookie)
  const ca = decodedCookie.split(";")
  for (let i = 0; i < ca.length; i++) {
    let c = ca[i]
    while (c.charAt(0) === " ") {
      c = c.substring(1)
    }
    if (c.indexOf(name) === 0) {
      return c.substring(name.length, c.length)
    }
  }
  return ""
}

/**
 * Function to remove all the cookies of the application
 */
export const deleteAllCookies = function() {
  const cookies = document.cookie.split(";")

  for (let i = 0; i < cookies.length; i++) {
    let cookie = cookies[i]
    let eqPos = cookie.indexOf("=")
    let name = eqPos > -1 ? cookie.substr(0, eqPos) : cookie
    document.cookie = name + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT"
  }
}

/**
 * Function that parses the JWT token and returns the Datetime of expiry
 * @param {string} token The JWT Token
 * @returns {Date} Time of expiry
 */
export const getExpiry = function(token) {
  const parts = token.split(".")
  let info = parts[1].replace("-", "+").replace("_", "/")
  info = JSON.parse(window.atob(info))
  return new Date(info.exp * 1000)
}

/**
 * Function that would return the value of 'identity' stored in the JWT if
 * present, return the string 'User' otherwise.
 *
 * @param token The JWT Token to extract the identity from
 * @returns {Object} contains the name and Id of the user
 */
export const getIdentity = function(token) {
  if (typeof token !== "string" || !token || token.length === 0) {
    return { name: "Guest", id: 0 }
  }
  const parts = token.split(".")
  let info = parts[1].replace("-", "+").replace("_", "/")
  info = JSON.parse(window.atob(info))
  if (info.hasOwnProperty("identity")) {
    return info.identity
  }
  return { name: "Guest", id: 0 }
}

/**
 * Function that parses the input CSV of grader and recipients and returns
 *
 * @param {string} csvText
 *        A multiline string containing the graders and recipients as CSV
 * @returns {{pairs: Array, errors: Array}} where pairs is an array of objects
 *          of the format {grader: String, recipients: Array[String]} and errors
 *          is an array of strings
 */
export const parsePairingCSV = function(csvText) {
  let lines = csvText.split("\n")
  let pairs = []
  let errors = []

  for (let lno = 0; lno < lines.length; lno++) {
    let pair = {}
    let error = ""
    let line = lines[lno]

    // skip empty lines
    if (line.trim().length === 0) {
      continue
    }

    let students = line
      .split(",")
      .map(x => x.trim())
      .filter(x => x !== "")

    if (students.length < 2) {
      error = "Less than 2 students found in line " + (lno + 1) + ". "
      error += "Cannot find a valid Grader and Recipient pair."
      errors.push(error)
      continue
    }

    pair.grader = students[0]
    pair.recipients = students.slice(1)
    pairs.push(pair)
  }

  return { pairs, errors }
}

/**
 * Function to build the query string from the passed parameters
 *
 * @param {Object} params Key-Value pairs
 * @returns {string} a URL Encoded string of key1=value1&key2=value2&...
 */
export function queryString(params) {
  const esc = encodeURIComponent
  return Object.keys(params)
    .map(k => esc(k) + "=" + esc(params[k]))
    .join("&")
}

/**
 * Function that returns the initials for a name
 *
 * @param {string} name A users name
 * @returns {string} Initials of the user's name
 */
export function initials(name) {
  if (typeof name === "undefined") return

  let parts = name.split(" ")
  return parts.reduce((acc, curr) => acc + curr.charAt(0), "")
}

/**
 * Function that takes in a feedback object and returns the discussion page URL
 *
 * @param {Object} feedback
 * @returns {{name: string, params: {assignment_id: Number, course_id: Number, user_id: Number}}}
 */
export function feedbackLink(feedback) {
  return {
    name: "give-feedback",
    params: {
      course_id: feedback.course_id,
      assignment_id: feedback.assignment_id,
      user_id: feedback.receiver.id
    }
  }
}

/**
 * Vue Filter to display the DateTime object in a custom format
 *
 * @param {string} value ISO formatted date string to format
 * @returns {string} custom formatted string of the date
 */
export function readableDate(value) {
  let d = new Date(value)

  if (!(d instanceof Date) || isNaN(d)) return value

  return d.toLocaleString({
    weekday: "long",
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "numeric",
    timeZoneName: "long"
  })
}

/**
 * Vue Filter to display short dates
 *
 * @param {String} value ISO string of the date to format
 * @returns {string} custom formatted string of the date
 */
export function shortDate(value) {
  if (value === null) return "N/A"
  let d = new Date(value)
  if (!(d instanceof Date) || isNaN(d)) return value
  let options = {
    month: "short",
    day: "numeric",
    year: "numeric"
  }
  return d.toLocaleDateString(undefined, options)
}

/**
 * Vue Filter to display short times
 *
 * @param {String} value ISO string of the date to format
 * @returns {string} custom formatted string of the date
 */
export function shortTime(value) {
  let d = new Date(value)
  if (!(d instanceof Date) || isNaN(d)) return value
  return d.toLocaleTimeString("en-US", { hour: "numeric", minute: "numeric" })
}

/**
 * Vue Filter to clamp text. Adds clamp value or '...' after the specified
 * length if the input string exceeds the length specified in the argument.
 *
 * @param {String} text Input text
 * @param {Number} length The length at which the text should be truncated
 * @param {String} clamp The string to append when text exceeds length. Defaults
 *        to '...' if not provided
 * @param {boolean} on Flag to perform or skip clamping
 * @returns {string} clamped text
 */
export function truncate(text, length, clamp, on) {
  if (!on) {
    return text
  }

  clamp = clamp || "..."
  let node = document.createElement("div")
  node.innerHTML = text
  let content = node.textContent
  return content.length > length ? content.slice(0, length) + clamp : content
}
