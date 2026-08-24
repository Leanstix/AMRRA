export const API_BASE = (process.env.NEXT_PUBLIC_AMRRA_API_URL || "http://localhost:8000/api/v1").replace(/\/$/, "")

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
  const stages = ["ingestion", "retrieval", "extraction", "planning", "experimentation", "judging"]
  const completed = new Set(
    (run?.traces || [])
      .filter((trace) => trace.status === "completed")
      .map((trace) => trace.stage),
  )
  return stages.map((stage) => ({ stage, completed: completed.has(stage) }))
}
