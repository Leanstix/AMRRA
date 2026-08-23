import test from "node:test"
import assert from "node:assert/strict"
import { stageProgress } from "../lib/amrra-client.mjs"

test("stageProgress reports only persisted completed stages", () => {
  const result = stageProgress({ traces: [
    { stage: "ingestion", status: "completed" },
    { stage: "retrieval", status: "completed" },
    { stage: "extraction", status: "failed" },
  ] })
  assert.equal(result.filter((item) => item.completed).length, 2)
  assert.equal(result.find((item) => item.stage === "extraction").completed, false)
})

test("stageProgress always exposes the six-stage agent workflow", () => {
  assert.deepEqual(
    stageProgress(null).map((item) => item.stage),
    ["ingestion", "retrieval", "extraction", "planning", "experimentation", "judging"],
  )
})
