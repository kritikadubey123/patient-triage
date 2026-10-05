// Thin wrapper around fetch(). Components never call fetch directly; they go
// through the hooks, which go through this file.
const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";

export class ApiError extends Error {
  constructor(message, { status = 0, fieldErrors = {} } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.fieldErrors = fieldErrors; // e.g. { heart_rate: "must be between 30 and 220 bpm" }
  }
}

async function buildError(response) {
  let body = null;
  try {
    body = await response.json();
  } catch {
    // Response had no JSON body; fall through to the generic message.
  }
  const detail = body?.detail;

  // FastAPI returns 422 with a list like:
  // [{ loc: ["body", "heart_rate"], msg: "Value error, heart_rate must be ..." }]
  if (response.status === 422 && Array.isArray(detail)) {
    const fieldErrors = {};
    for (const item of detail) {
      const field = item.loc?.[item.loc.length - 1];
      if (typeof field === "string") {
        fieldErrors[field] = item.msg.replace(/^Value error, /, "");
      }
    }
    return new ApiError("Please fix the highlighted fields.", { status: 422, fieldErrors });
  }

  // Other errors from our API use a plain string: { detail: "Could not save..." }
  const message = typeof detail === "string" ? detail : `Request failed (${response.status})`;
  return new ApiError(message, { status: response.status });
}

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
  } catch (err) {
    if (err.name === "AbortError") throw err; // caller cancelled on purpose
    throw new ApiError("Cannot reach the server. Is the backend running on port 8000?");
  }

  if (!response.ok) throw await buildError(response);
  return response.json();
}

export const fetchQueue = (signal) => request("/queue", { signal });

export const createTriage = (payload) =>
  request("/triage", { method: "POST", body: JSON.stringify(payload) });