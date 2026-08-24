"use client"

import { useEffect, useMemo, useRef, useState } from "react"
import { AgentStageCard } from "@/components/agent/agent-stage-card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { createRun, fetchRun, stageProgress, STAGE_ORDER } from "@/lib/amrra-client.mjs"
import {
  AlertCircle,
  ArrowRight,
  BrainCircuit,
  Check,
  ChevronRight,
  FileText,
  Layers3,
  Link2,
  Loader2,
  Microscope,
  Paperclip,
  RotateCcw,
  ShieldCheck,
  Sparkles,
  UploadCloud,
  X,
} from "lucide-react"

const TERMINAL = new Set(["completed", "failed"])
const MAX_PDF_BYTES = 10 * 1024 * 1024

function stageLabel(stage) {
  return stage ? stage.charAt(0).toUpperCase() + stage.slice(1) : "Ready"
}

function runStatusLabel(status) {
  if (!status) return "Ready"
  return status.charAt(0).toUpperCase() + status.slice(1)
}

function runStatusClass(status) {
  if (status === "completed") return "border-emerald-500/20 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300"
  if (status === "failed") return "border-destructive/25 bg-destructive/10 text-destructive"
  if (status === "running") return "border-primary/20 bg-primary/10 text-primary"
  return "border-border bg-muted/50 text-muted-foreground"
}

export function ResearchWorkbench() {
  const [query, setQuery] = useState("")
  const [url, setUrl] = useState("")
  const [text, setText] = useState("")
  const [file, setFile] = useState(null)
  const [run, setRun] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState("")
  const [dragActive, setDragActive] = useState(false)
  const [openStages, setOpenStages] = useState(() => new Set())
  const timer = useRef(null)
  const autoOpenedStage = useRef(null)

  useEffect(() => () => timer.current && clearInterval(timer.current), [])

  const progress = useMemo(() => stageProgress(run), [run])
  const completedCount = progress.filter((item) => item.completed).length
  const percent = run?.status === "completed" ? 100 : Math.round((completedCount / progress.length) * 100)
  const activeStage = progress.find((item) => item.status === "active")?.stage || null

  useEffect(() => {
    const stageToOpen = activeStage || (run?.status === "completed" ? "judging" : null)
    if (!stageToOpen || autoOpenedStage.current === stageToOpen) return
    autoOpenedStage.current = stageToOpen
    setOpenStages((current) => {
      const next = new Set(current)
      next.add(stageToOpen)
      return next
    })
  }, [activeStage, run?.status])

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
      if (timer.current) {
        clearInterval(timer.current)
        timer.current = null
      }
    }
  }

  function acceptFile(candidate) {
    if (!candidate) return
    const isPdf = candidate.type === "application/pdf" || candidate.name?.toLowerCase().endsWith(".pdf")
    if (!isPdf) {
      setError("AMRRA currently accepts PDF uploads for file-based research material.")
      return
    }
    if (candidate.size > MAX_PDF_BYTES) {
      setError("PDF uploads must be 10 MB or smaller.")
      return
    }
    setError("")
    setFile(candidate)
  }

  function handleDrop(event) {
    event.preventDefault()
    setDragActive(false)
    acceptFile(event.dataTransfer.files?.[0])
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
    setOpenStages(new Set())
    autoOpenedStage.current = null
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

  function setStageOpen(stage, open) {
    setOpenStages((current) => {
      const next = new Set(current)
      if (open) next.add(stage)
      else next.delete(stage)
      return next
    })
  }

  function resetRunView() {
    if (timer.current) {
      clearInterval(timer.current)
      timer.current = null
    }
    setRun(null)
    setError("")
    setOpenStages(new Set())
    autoOpenedStage.current = null
  }

  const completedExperiments = run?.experiments?.filter((item) => item.status === "completed").length || 0
  const hypothesisCount = run?.extraction?.hypotheses?.length || 0

  return (
    <div className="space-y-8">
      <section className="animate-fade-up relative overflow-hidden rounded-[2rem] border bg-card/70 px-5 py-7 premium-shadow hairline-highlight sm:px-7 md:px-9 md:py-9">
        <div className="pointer-events-none absolute -right-24 -top-28 h-72 w-72 rounded-full bg-primary/10 blur-3xl" />
        <div className="pointer-events-none absolute bottom-0 right-20 h-44 w-44 rounded-full bg-accent/55 blur-3xl" />
        <div className="relative grid gap-7 xl:grid-cols-[1fr_auto] xl:items-end">
          <div className="max-w-4xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-primary/15 bg-primary/8 px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.2em] text-primary">
              <Sparkles className="h-3.5 w-3.5" />
              Evidence-grounded agentic research
            </div>
            <h1 className="mt-5 max-w-3xl text-balance text-4xl font-semibold tracking-[-0.045em] sm:text-5xl lg:text-[3.45rem] lg:leading-[1.04]">
              Research with an <span className="text-primary">audit trail.</span>
            </h1>
            <p className="mt-4 max-w-2xl text-sm leading-7 text-muted-foreground sm:text-[15px]">
              AMRRA coordinates probabilistic evidence reasoning with deterministic statistical validation. Every stage stays inspectable, grounded and independently collapsible.
            </p>
          </div>
          <div className="grid grid-cols-3 gap-2 xl:w-[22rem]">
            <HeroMetric value="06" label="persisted stages" />
            <HeroMetric value="04" label="statistical tools" />
            <HeroMetric value="01" label="evidence boundary" />
          </div>
        </div>
      </section>

      <div className="grid items-start gap-6 xl:grid-cols-[minmax(21rem,0.72fr)_minmax(34rem,1.28fr)]">
        <Card className="glass-panel premium-shadow overflow-hidden border-border/80 xl:sticky xl:top-8">
          <div className="border-b bg-card/55 px-5 py-5 sm:px-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary">Research brief</p>
                <h2 className="mt-1 text-lg font-semibold tracking-[-0.02em]">Define the question and evidence</h2>
              </div>
              <div className="grid h-9 w-9 place-items-center rounded-xl bg-primary/10 text-primary"><Microscope className="h-4 w-4" /></div>
            </div>
          </div>

          <form onSubmit={submit} className="space-y-5 p-5 sm:p-6">
            <div className="space-y-2">
              <div className="flex items-center justify-between gap-3">
                <label htmlFor="research-question" className="text-xs font-semibold">Research question</label>
                <span className="text-[10px] text-muted-foreground">{query.length}/1000</span>
              </div>
              <Textarea
                id="research-question"
                value={query}
                maxLength={1000}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="What should AMRRA investigate, compare or test?"
                className="min-h-32 resize-y rounded-xl border-input/80 bg-background/70 px-3.5 py-3 text-sm leading-6 shadow-inner shadow-foreground/[0.02] transition focus:bg-background"
              />
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold">Evidence pack</p>
                  <p className="mt-0.5 text-[10px] text-muted-foreground">PDF, URL and pasted text can be combined.</p>
                </div>
                <Paperclip className="h-4 w-4 text-muted-foreground" />
              </div>

              <label
                className={`group relative flex cursor-pointer items-center gap-3 rounded-2xl border border-dashed p-4 transition-all duration-200 ${
                  dragActive ? "border-primary bg-primary/8 shadow-inner" : "border-border bg-muted/20 hover:border-primary/35 hover:bg-primary/5"
                }`}
                onDragEnter={(event) => { event.preventDefault(); setDragActive(true) }}
                onDragOver={(event) => event.preventDefault()}
                onDragLeave={() => setDragActive(false)}
                onDrop={handleDrop}
              >
                <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl border bg-background text-primary shadow-sm transition-transform duration-200 group-hover:-translate-y-0.5">
                  {file ? <FileText className="h-4 w-4" /> : <UploadCloud className="h-4 w-4" />}
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-xs font-semibold">{file ? file.name : "Drop a research PDF here"}</span>
                  <span className="mt-1 block text-[10px] text-muted-foreground">{file ? `${(file.size / 1024 / 1024).toFixed(2)} MB · ready to ingest` : "or click to browse · max 10 MB"}</span>
                </span>
                {file && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="relative z-10 h-8 w-8 rounded-lg"
                    onClick={(event) => { event.preventDefault(); setFile(null) }}
                    aria-label="Remove PDF"
                  >
                    <X className="h-3.5 w-3.5" />
                  </Button>
                )}
                <Input
                  type="file"
                  accept="application/pdf,.pdf"
                  className="hidden"
                  onChange={(event) => acceptFile(event.target.files?.[0])}
                />
              </label>

              <div className="relative py-1">
                <div className="absolute inset-x-0 top-1/2 border-t" />
                <span className="relative mx-auto block w-fit bg-card px-2 text-[9px] font-bold uppercase tracking-[0.18em] text-muted-foreground">optional additions</span>
              </div>

              <div className="relative">
                <Link2 className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
                <Input
                  value={url}
                  onChange={(event) => setUrl(event.target.value)}
                  placeholder="Public paper or article URL"
                  className="h-10 rounded-xl bg-background/70 pl-9 text-xs"
                />
              </div>
              <Textarea
                value={text}
                onChange={(event) => setText(event.target.value)}
                placeholder="Or paste an abstract, results section, table or reproducibility evidence…"
                className="min-h-24 rounded-xl bg-background/70 text-xs leading-5"
              />
            </div>

            {error && (
              <div className="animate-soft-in flex gap-2.5 rounded-xl border border-destructive/25 bg-destructive/6 p-3 text-xs leading-5 text-destructive" role="alert">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <Button type="submit" size="lg" className="group h-11 w-full rounded-xl shadow-lg shadow-primary/15" disabled={submitting || run?.status === "running"}>
              {submitting ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Starting research run…</>
              ) : run?.status === "running" ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" />AMRRA is working…</>
              ) : (
                <><BrainCircuit className="mr-2 h-4 w-4" />Run AMRRA agent<ArrowRight className="ml-2 h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5" /></>
              )}
            </Button>

            <div className="flex items-center justify-center gap-2 text-[10px] text-muted-foreground">
              <ShieldCheck className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
              Unsupported statistics are refused rather than fabricated.
            </div>
          </form>
        </Card>

        <Card className="glass-panel premium-shadow overflow-hidden border-border/80">
          <div className="border-b bg-card/55 px-5 py-5 sm:px-6">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary">Agent execution console</p>
                  <Badge variant="outline" className={`h-6 rounded-full px-2 text-[10px] ${runStatusClass(run?.status)}`} aria-live="polite">
                    {run?.status === "running" && <span className="mr-1.5 h-1.5 w-1.5 rounded-full bg-primary animate-status-pulse" />}
                    {runStatusLabel(run?.status)}
                  </Badge>
                </div>
                <h2 className="mt-1 text-lg font-semibold tracking-[-0.02em]">Six-stage research trace</h2>
                <p className="mt-1 text-xs leading-5 text-muted-foreground">Open any stage to inspect its work. Collapse it again when you want a cleaner view.</p>
              </div>
              <div className="flex items-center gap-2">
                <Button type="button" variant="ghost" size="sm" className="h-8 rounded-lg px-2.5 text-[10px]" onClick={() => setOpenStages(new Set())}>Hide all</Button>
                <Button type="button" variant="outline" size="sm" className="h-8 rounded-lg px-2.5 text-[10px]" onClick={() => setOpenStages(new Set(STAGE_ORDER))}>Inspect all</Button>
                {run && <Button type="button" variant="ghost" size="icon" className="h-8 w-8 rounded-lg" onClick={resetRunView} aria-label="Clear run view"><RotateCcw className="h-3.5 w-3.5" /></Button>}
              </div>
            </div>

            <div className="mt-5">
              <div className="mb-2 flex items-center justify-between gap-4 text-[10px] font-medium text-muted-foreground">
                <span>{run?.status === "completed" ? "All stages complete" : activeStage ? `${stageLabel(activeStage)} is working` : run?.status === "queued" ? "Run queued" : "Ready for a research run"}</span>
                <span className="font-mono">{percent}%</span>
              </div>
              <div className="animate-progress-shine h-2 overflow-hidden rounded-full bg-muted/80">
                <div className="h-full rounded-full bg-gradient-to-r from-primary via-primary to-cyan-500 transition-[width] duration-700 ease-out" style={{ width: `${percent}%` }} />
              </div>
              {run?.run_id && <p className="mt-2 truncate font-mono text-[9px] text-muted-foreground/70">run:{run.run_id}</p>}
            </div>
          </div>

          <div className="space-y-2.5 p-4 sm:p-5">
            {progress.map((item, index) => (
              <AgentStageCard
                key={item.stage}
                item={item}
                run={run}
                index={index}
                open={openStages.has(item.stage)}
                onOpenChange={(open) => setStageOpen(item.stage, open)}
              />
            ))}
          </div>

          {run?.error_message && (
            <div className="mx-4 mb-4 flex gap-3 rounded-2xl border border-destructive/25 bg-destructive/7 p-4 text-xs text-destructive sm:mx-5 sm:mb-5">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              <div>
                <p className="font-semibold">{run.error_code || "Run failed"}</p>
                <p className="mt-1 leading-5">{run.error_message}</p>
              </div>
            </div>
          )}
        </Card>
      </div>

      {run?.report && (
        <section className="animate-fade-up grid gap-4 lg:grid-cols-[0.72fr_1.28fr]" style={{ animationDelay: "90ms" }}>
          <div className="grid grid-cols-3 gap-3 lg:grid-cols-1">
            <SummaryMetric label="Grounded hypotheses" value={hypothesisCount} detail="validated against evidence IDs" />
            <SummaryMetric label="Completed experiments" value={completedExperiments} detail="deterministic tool executions" />
            <SummaryMetric label="Judge confidence" value={`${Math.round((run.report.confidence || 0) * 100)}%`} detail="final synthesis confidence" />
          </div>
          <Card className="premium-shadow overflow-hidden border-primary/15 bg-gradient-to-br from-card via-card to-primary/5 p-5 sm:p-6">
            <div className="flex items-start gap-4">
              <div className="grid h-11 w-11 shrink-0 place-items-center rounded-2xl bg-primary text-primary-foreground shadow-lg shadow-primary/20"><Check className="h-5 w-5" /></div>
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary">Final research assessment</p>
                  <Badge variant="outline" className="rounded-full text-[10px]">traceable</Badge>
                </div>
                <h2 className="mt-1 text-xl font-semibold tracking-[-0.025em]">{run.report.title}</h2>
              </div>
            </div>
            <p className="mt-5 text-sm leading-7 text-muted-foreground">{run.report.summary}</p>
            <div className="mt-5 rounded-2xl border border-primary/15 bg-primary/7 p-4">
              <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-primary">Conclusion</p>
              <p className="mt-2 text-sm font-medium leading-7">{run.report.conclusion}</p>
            </div>
            <button
              type="button"
              className="mt-4 inline-flex items-center gap-1.5 text-xs font-semibold text-primary transition hover:gap-2"
              onClick={() => setStageOpen("judging", true)}
            >
              Inspect Judge evidence and limitations <ChevronRight className="h-3.5 w-3.5" />
            </button>
          </Card>
        </section>
      )}
    </div>
  )
}

function HeroMetric({ value, label }) {
  return (
    <div className="rounded-2xl border bg-background/55 p-3 text-center backdrop-blur-sm">
      <div className="font-mono text-lg font-semibold tracking-[-0.03em] text-foreground">{value}</div>
      <div className="mt-1 text-[9px] font-bold uppercase leading-4 tracking-[0.15em] text-muted-foreground">{label}</div>
    </div>
  )
}

function SummaryMetric({ label, value, detail }) {
  return (
    <Card className="premium-shadow flex min-w-0 flex-col justify-center p-4 sm:p-5">
      <div className="flex items-center gap-2 text-[9px] font-bold uppercase tracking-[0.16em] text-muted-foreground"><Layers3 className="h-3.5 w-3.5" />{label}</div>
      <p className="mt-2 text-2xl font-semibold tracking-[-0.04em]">{value}</p>
      <p className="mt-1 hidden text-[10px] leading-4 text-muted-foreground sm:block">{detail}</p>
    </Card>
  )
}
