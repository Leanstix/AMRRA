"use client"

import { useEffect, useMemo, useRef, useState } from "react"
import { createRun, fetchRun, stageProgress } from "@/lib/amrra-client.mjs"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Progress } from "@/components/ui/progress"
import { Textarea } from "@/components/ui/textarea"
import {
  AlertCircle,
  BrainCircuit,
  CheckCircle2,
  FileText,
  Loader2,
  Microscope,
  Upload,
} from "lucide-react"

const TERMINAL = new Set(["completed", "failed"])

function formatStage(stage) {
  return stage.charAt(0).toUpperCase() + stage.slice(1)
}

export function ResearchWorkbench() {
  const [query, setQuery] = useState("")
  const [url, setUrl] = useState("")
  const [text, setText] = useState("")
  const [file, setFile] = useState(null)
  const [run, setRun] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState("")
  const timer = useRef(null)

  useEffect(() => () => timer.current && clearInterval(timer.current), [])

  const progress = useMemo(() => stageProgress(run), [run])
  const percent = progress.length
    ? Math.round((progress.filter((item) => item.completed).length / progress.length) * 100)
    : 0

  async function refresh(runId) {
    try {
      const latest = await fetchRun(runId)
      setRun(latest)
      if (TERMINAL.has(latest.status) && timer.current) {
        clearInterval(timer.current)
        timer.current = null
      }
    } catch (err) {
      setError(err.message)
      if (timer.current) clearInterval(timer.current)
    }
  }

  async function submit(event) {
    event.preventDefault()
    setError("")
    if (!query.trim()) {
      setError("Enter the research question AMRRA should investigate.")
      return
    }
    if (!file && !url.trim() && !text.trim()) {
      setError("Provide a PDF, public URL, or source text.")
      return
    }

    setSubmitting(true)
    try {
      const created = await createRun({ query, url, text, file })
      setRun(created)
      if (timer.current) clearInterval(timer.current)
      timer.current = setInterval(() => refresh(created.run_id), 1500)
      await refresh(created.run_id)
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-primary">
          <BrainCircuit className="h-5 w-5" />
          <span className="text-sm font-medium">Agentic research workflow</span>
        </div>
        <h1 className="text-3xl font-bold tracking-tight academic-text">AMRRA Research Workbench</h1>
        <p className="max-w-3xl text-muted-foreground">
          Give AMRRA a research question and evidence. The agent retrieves relevant passages,
          extracts evidence-backed hypotheses, selects deterministic statistical tools, executes
          them, and judges the result with traceable citations.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <Card className="p-6">
          <form onSubmit={submit} className="space-y-5">
            <div className="space-y-2">
              <label className="text-sm font-medium">Research question</label>
              <Textarea
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="e.g. Does the intervention significantly improve recovery outcomes compared with the control?"
                className="min-h-24"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Research paper PDF</label>
              <label className="flex cursor-pointer items-center justify-between rounded-lg border border-dashed p-4 hover:bg-accent/30">
                <span className="flex items-center gap-3">
                  <Upload className="h-5 w-5 text-muted-foreground" />
                  <span className="text-sm">{file ? file.name : "Select a PDF (max 10 MB)"}</span>
                </span>
                <Input
                  type="file"
                  accept="application/pdf,.pdf"
                  className="hidden"
                  onChange={(event) => setFile(event.target.files?.[0] || null)}
                />
              </label>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Or public paper/article URL</label>
              <Input value={url} onChange={(event) => setUrl(event.target.value)} placeholder="https://..." />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Or paste source text</label>
              <Textarea
                value={text}
                onChange={(event) => setText(event.target.value)}
                placeholder="Paste an abstract, results section, or reproducibility evidence..."
                className="min-h-28"
              />
            </div>
            {error && (
              <div className="flex gap-2 rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                {error}
              </div>
            )}
            <Button type="submit" className="w-full" disabled={submitting}>
              {submitting ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Starting run...</>
              ) : (
                <><Microscope className="mr-2 h-4 w-4" />Run AMRRA agent</>
              )}
            </Button>
          </form>
        </Card>

        <div className="space-y-6">
          <Card className="p-6">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h2 className="font-semibold">Agent trace</h2>
                <p className="text-sm text-muted-foreground">Every stage is persisted and inspectable.</p>
              </div>
              {run && <Badge variant={run.status === "failed" ? "destructive" : "secondary"}>{run.status}</Badge>}
            </div>
            <Progress value={percent} className="mb-5" />
            <div className="grid gap-2 sm:grid-cols-2">
              {progress.map(({ stage, completed }) => (
                <div key={stage} className="flex items-center gap-2 rounded-md border p-3 text-sm">
                  {completed ? (
                    <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                  ) : run && !TERMINAL.has(run.status) ? (
                    <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                  ) : (
                    <div className="h-4 w-4 rounded-full border" />
                  )}
                  <span>{formatStage(stage)}</span>
                </div>
              ))}
            </div>
            {run?.error_message && (
              <div className="mt-4 rounded-md bg-destructive/5 p-3 text-sm text-destructive">
                <strong>{run.error_code}:</strong> {run.error_message}
              </div>
            )}
          </Card>

          {run?.extraction?.hypotheses?.length > 0 && (
            <Card className="p-6">
              <h2 className="mb-4 font-semibold">Evidence-backed hypotheses</h2>
              <div className="space-y-3">
                {run.extraction.hypotheses.map((hypothesis) => (
                  <div key={hypothesis.hypothesis_id} className="rounded-lg border p-4">
                    <div className="mb-2 flex items-start justify-between gap-4">
                      <p className="font-medium">{hypothesis.statement}</p>
                      <Badge variant="outline">{Math.round(hypothesis.confidence * 100)}%</Badge>
                    </div>
                    <p className="text-xs text-muted-foreground">Evidence: {hypothesis.evidence_chunk_ids.join(", ")}</p>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {run?.experiments?.length > 0 && (
            <Card className="p-6">
              <h2 className="mb-4 font-semibold">Deterministic experiments</h2>
              <div className="space-y-3">
                {run.experiments.map((result) => (
                  <div key={result.hypothesis_id} className="rounded-lg border p-4">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge>{result.test_used}</Badge>
                      <Badge variant="outline">{result.status}</Badge>
                    </div>
                    <div className="mt-3 grid grid-cols-2 gap-3 text-sm md:grid-cols-4">
                      <div><span className="text-muted-foreground">p-value</span><div className="font-mono">{result.p_value ?? "—"}</div></div>
                      <div><span className="text-muted-foreground">effect</span><div className="font-mono">{result.effect_size ?? "—"}</div></div>
                      <div className="col-span-2"><span className="text-muted-foreground">conclusion</span><div>{result.conclusion}</div></div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {run?.report && (
            <Card className="p-6">
              <div className="mb-3 flex items-center gap-2"><FileText className="h-5 w-5" /><h2 className="font-semibold">{run.report.title}</h2></div>
              <p className="text-sm leading-6">{run.report.summary}</p>
              <div className="mt-4 rounded-md bg-accent/30 p-4"><strong>Conclusion:</strong> {run.report.conclusion}</div>
              {run.report.limitations?.length > 0 && (
                <div className="mt-4">
                  <h3 className="text-sm font-medium">Limitations</h3>
                  <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-muted-foreground">
                    {run.report.limitations.map((item) => <li key={item}>{item}</li>)}
                  </ul>
                </div>
              )}
              {run.report.citations?.length > 0 && (
                <div className="mt-4">
                  <h3 className="text-sm font-medium">Traceable citations</h3>
                  <div className="mt-2 space-y-2">
                    {run.report.citations.map((citation, index) => (
                      <div key={`${citation.chunk_id}-${index}`} className="rounded border p-3 text-sm">
                        <span className="font-mono text-xs text-muted-foreground">{citation.chunk_id}</span>
                        <p>{citation.claim}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
