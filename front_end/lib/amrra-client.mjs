export const API_BASE = (process.env.NEXT_PUBLIC_AMRRA_API_URL || "http://localhost:8000/api/v1").replace(/\/$/, "")

export const STAGE_ORDER = ["ingestion", "retrieval", "extraction", "planning", "experimentation", "judging"]

const HTTP_URL_PATTERN = /https?:\/\/[^\s<>"']+/gi
const TRAILING_URL_PUNCTUATION = /[.,!?;:\]\)}]+$/

export function extractHttpUrls(value = "") {
  const matches = String(value).match(HTTP_URL_PATTERN) || []
  return [...new Set(matches.map((url) => url.replace(TRAILING_URL_PUNCTUATION, "")).filter(Boolean))]
}

export async function createRun({ query, url, text, file, topK = 8 }) {
  const form = new FormData()
  form.append("query", query)
  form.append("top_k", String(topK))
  if (url?.trim()) form.append("url", url.trim())
  if (text?.trim()) form.append("text", text.trim())
  if (file) form.append("file", file)

  const response = await fetch(`${API_BASE}/runs`, { method: "POST", body: form })
  if (!response.ok) throw await toApiError(response)
  return response.json()
}

export async function fetchRun(runId) {
  const response = await fetch(`${API_BASE}/runs/${encodeURIComponent(runId)}`, { cache: "no-store" })
  if (!response.ok) throw await toApiError(response)
  return response.json()
}

export async function toApiError(response) {
  let message = `Request failed with status ${response.status}`
  try {
    const body = await response.json()
    if (typeof body.detail === "string") message = body.detail
    else if (body.detail) message = JSON.stringify(body.detail)
  } catch (_) {}
  const error = new Error(message)
  error.status = response.status
  return error
}

export function stageProgress(run) {
  const traceByStage = new Map()
  for (const trace of run?.traces || []) {
    traceByStage.set(trace.stage, trace)
  }

  const result = STAGE_ORDER.map((stage) => {
    const trace = traceByStage.get(stage) || null
    const completed = trace?.status === "completed"
    const failed = trace?.status === "failed"
    return {
      stage,
      completed,
      trace,
      status: failed ? "failed" : completed ? "completed" : "pending",
    }
  })

  if (run?.status === "running") {
    const active = result.find((item) => item.status === "pending")
    if (active) active.status = "active"
  }

  return result
}
