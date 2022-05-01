import axios from "axios"

export default {
  getAllCourses(cb, errCb) {
    axios
      .get("/api/courses/")
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  getCourse(course_id, cb, errCb) {
    axios
      .get(`/api/course/${course_id}/`)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  getStudents(course_id, cb, errCb) {
    axios
      .get(`/api/course/${course_id}/students/`)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  getTAs(course_id, cb, errCb) {
    axios
      .get(`/api/course/${course_id}/tas/`)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  initializeCourse(course_id, cb, errCb) {
    axios
      .post(`/api/course/${course_id}/initialize/`)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  getData(data, cb, errCb) {
    axios
      .post(`/api/course/${data.course_id}/data/`, data)
      .then(resp => cb(resp.data))
      .catch(err => errCb(err))
  },
  updateCourseSettings: function(data, cb, errCb) {
    axios
      .post(`/api/course/${data.course_id}/course-wide-settings/`, data)
      .then(res => cb(res.data))
      .catch(err => errCb(err))
  }
}
