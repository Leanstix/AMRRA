import test from "node:test"
import assert from "node:assert/strict"
import { STAGE_ORDER, stageProgress } from "../lib/amrra-client.mjs"

test("stageProgress reports persisted completed and failed stages", () => {
  const result = stageProgress({
    status: "failed",
    traces: [
      { stage: "ingestion", status: "completed", latency_ms: 12 },
      { stage: "retrieval", status: "completed", latency_ms: 44 },
      { stage: "extraction", status: "failed", error_code: "BROKEN" },
    ],
  })

  assert.equal(result.filter((item) => item.completed).length, 2)
  assert.equal(result.find((item) => item.stage === "extraction").status, "failed")
  assert.equal(result.find((item) => item.stage === "extraction").completed, false)
  assert.equal(result.find((item) => item.stage === "retrieval").trace.latency_ms, 44)
})

test("stageProgress marks the first incomplete stage active while a run is running", () => {
  const result = stageProgress({
    status: "running",
    traces: [
      { stage: "ingestion", status: "completed" },
      { stage: "retrieval", status: "completed" },
    ],
  })

  assert.equal(result.find((item) => item.stage === "extraction").status, "active")
  assert.equal(result.find((item) => item.stage === "planning").status, "pending")
})

test("stageProgress always exposes the stable six-stage agent workflow", () => {
  assert.deepEqual(stageProgress(null).map((item) => item.stage), STAGE_ORDER)
  assert.equal(stageProgress(null).every((item) => item.status === "pending"), true)
})
