export const HOST = process.env.E2E_HOST
  ? `http://${process.env.E2E_HOST}`
  : "http://localhost:4000"

export const ADMIN_USER = process.env.ADMIN_USER || "canvas@example.edu"
export const ADMIN_PASS = process.env.ADMIN_PASS || "canvas-docker"
export const STUDENT_PASS = process.env.STUDENT_PASS || "secure123"
export const STUDY_STUDENT_NUMBER =
  HOST.indexOf("peerfeedback.io") === -1 ? "1" : "9"
