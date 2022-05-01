export const CANVAS_BASE_URL =
  process.env.NODE_ENV === "production"
    ? "https://gatech.instructure.com"
    : "http://localhost:3000"
