"use client"

import { useEffect, useMemo, useRef, useState } from "react"
import { AgentStageCard } from "@/components/agent/agent-stage-card"
import { ChatComposer } from "@/components/agent/chat-composer"
import { AssistantIdentity, UserResearchMessage } from "@/components/agent/conversation-message"
import { ResearchAnswer } from "@/components/agent/research-answer"
import { Badge } from "@/components/ui/badge"
import { createRun, extractHttpUrls, fetchRun, stageProgress } from "@/lib/amrra-client.mjs"
import {
  AlertCircle,
  BrainCircuit,
  CheckCircle2,
  Microscope,
  ShieldCheck,
  Sparkles,
} from "lucide-react"

const TERMINAL = new Set(["completed", "failed"])

function formatStage(stage) {
  if (!stage) return "Preparing"
  return stage.charAt(0).toUpperCase() + stage.slice(1)
}

function ProcessingView({ run, progress, openStages, setStageOpen }) {
  const completed = progress.filter((item) => item.completed).length
  const activeStage = progress.find((item) => item.status === "active")?.stage || null
  const percent = Math.round((completed / progress.length) * 100)

  return (
    <div className="animate-soft-in py-4">
      <AssistantIdentity working />
      <div className="mt-4 pl-0 sm:pl-9">
        <div className="rounded-2xl border bg-card/60 p-4 shadow-sm sm:p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm font-semibold">Working through the research pipeline</p>
              <p className="mt-1 text-xs text-muted-foreground">
                {activeStage ? `${formatStage(activeStage)} is currently running.` : "The worker is preparing the next stage."}
              </p>
            </div>
            <Badge variant="outline" className="rounded-full border-primary/15 bg-primary/5 text-[10px] text-primary">
              {completed}/{progress.length} stages
            </Badge>
          </div>

          <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-muted">
            <div
              className="animate-progress-shine h-full rounded-full bg-primary transition-[width] duration-700 ease-out"
              style={{ width: `${Math.max(percent, run?.status === "running" ? 4 : 0)}%` }}
            />
          </div>

          <div className="mt-4 space-y-2">
            {progress.map((item, index) => (
              <AgentStageCard
                key={item.stage}
                stage={item.stage}
                status={item.status}
                trace={item.trace}
                run={run}
                index={index}
                open={openStages.has(item.stage)}
                onOpenChange={(open) => setStageOpen(item.stage, open)}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function FailedRun({ run, progress, openStages, setStageOpen }) {
  return (
    <div className="animate-soft-in py-4">
      <AssistantIdentity />
      <div className="mt-4 space-y-4 pl-0 sm:pl-9">
        <div className="rounded-2xl border border-destructive/20 bg-destructive/[0.055] p-4 text-sm">
          <div className="flex gap-2.5">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-destructive" />
            <div>
              <p className="font-semibold text-destructive">The research run stopped before completion.</p>
              <p className="mt-1 leading-6 text-foreground/80">{run?.error_message || "An unexpected pipeline error occurred."}</p>
              {run?.error_code && <p className="mt-2 font-mono text-[10px] text-muted-foreground">{run.error_code}</p>}
            </div>
          </div>
        </div>

        <div className="rounded-2xl border bg-card/60 p-4">
          <p className="mb-3 text-xs font-semibold">Last visible process state</p>
          <div className="space-y-2">
            {progress.map((item, index) => (
              <AgentStageCard
                key={item.stage}
                stage={item.stage}
                status={item.status}
                trace={item.trace}
                run={run}
                index={index}
                open={openStages.has(item.stage)}
                onOpenChange={(open) => setStageOpen(item.stage, open)}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export function ResearchWorkbench() {
  const [draft, setDraft] = useState("")
  const [file, setFile] = useState(null)
  const [submitted, setSubmitted] = useState(null)
  const [run, setRun] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState("")
  const [openStages, setOpenStages] = useState(() => new Set())
  const timer = useRef(null)
  const autoOpenedStage = useRef(null)
  const conversationEnd = useRef(null)

  useEffect(() => () => timer.current && clearInterval(timer.current), [])

  const progress = useMemo(() => stageProgress(run), [run])
  const activeStage = progress.find((item) => item.status === "active")?.stage || null
  const isWorking = submitting || run?.status === "queued" || run?.status === "running"
  const hasConversation = Boolean(submitted || run)

  useEffect(() => {
    if (!activeStage || autoOpenedStage.current === activeStage) return
    autoOpenedStage.current = activeStage
    setOpenStages((current) => {
      const next = new Set(current)
      next.add(activeStage)
      return next
    })
  }, [activeStage])

  useEffect(() => {
    if (run?.status === "completed") {
      // Once all stages are complete the implementation trace disappears.
      // The conversation becomes result-first instead of exposing process noise.
      setOpenStages(new Set())
    }
  }, [run?.status])

  useEffect(() => {
    if (hasConversation) conversationEnd.current?.scrollIntoView({ behavior: "smooth", block: "end" })
  }, [run?.status, activeStage, hasConversation])

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

  async function submit() {
    const message = draft.trim()
    if (!message || isWorking) return

    const detectedUrls = extractHttpUrls(message)
    if (!file && detectedUrls.length === 0) {
      setError("Attach a research PDF with + or include a public http(s) link in your message.")
      return
    }

    const attachmentName = file?.name || null
    const requestFile = file

    if (timer.current) {
      clearInterval(timer.current)
      timer.current = null
    }

    setError("")
    setSubmitting(true)
    setSubmitted({ text: message, attachmentName, urls: detectedUrls })
    setRun(null)
    setOpenStages(new Set())
    autoOpenedStage.current = null

    try {
      const created = await createRun({
        query: message,
        url: detectedUrls[0] || "",
        text: "",
        file: requestFile,
      })
      setRun(created)
      setDraft("")
      setFile(null)
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

  if (!hasConversation) {
    return (
      <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center py-10 sm:min-h-[calc(100vh-5rem)]">
        <div className="animate-fade-up w-full max-w-3xl">
          <div className="mx-auto mb-7 max-w-xl text-center">
            <div className="mx-auto grid h-11 w-11 place-items-center rounded-2xl bg-foreground text-background shadow-lg shadow-foreground/10">
              <BrainCircuit className="h-5 w-5" />
            </div>
            <h1 className="mt-5 text-3xl font-semibold tracking-[-0.04em] sm:text-4xl">What are you researching?</h1>
            <p className="mx-auto mt-3 max-w-lg text-sm leading-6 text-muted-foreground">
              Ask a research question, attach a PDF or paste a public paper link. AMRRA will ground the evidence, choose defensible tools and return the result.
            </p>
          </div>

          <ChatComposer
            value={draft}
            onChange={setDraft}
            file={file}
            onFileChange={setFile}
            onSubmit={submit}
            disabled={isWorking}
            busy={isWorking}
            onValidationError={setError}
          />

          {error && (
            <div className="mx-auto mt-3 flex max-w-2xl items-start gap-2 rounded-xl px-3 py-2 text-xs text-destructive" role="alert">
              <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="mt-5 flex flex-wrap items-center justify-center gap-x-5 gap-y-2 text-[10px] text-muted-foreground">
            <span className="inline-flex items-center gap-1.5"><ShieldCheck className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />Evidence-grounded</span>
            <span className="inline-flex items-center gap-1.5"><Microscope className="h-3.5 w-3.5" />Deterministic statistics</span>
            <span className="inline-flex items-center gap-1.5"><Sparkles className="h-3.5 w-3.5" />Traceable judgement</span>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto flex min-h-[calc(100vh-4rem)] w-full max-w-4xl flex-col sm:min-h-[calc(100vh-5rem)]">
      <div className="flex-1 pb-6 pt-2 sm:pt-4">
        {submitted && <UserResearchMessage text={submitted.text} attachmentName={submitted.attachmentName} />}

        {isWorking && <ProcessingView run={run} progress={progress} openStages={openStages} setStageOpen={setStageOpen} />}
        {run?.status === "failed" && <FailedRun run={run} progress={progress} openStages={openStages} setStageOpen={setStageOpen} />}
        {run?.status === "completed" && <ResearchAnswer run={run} />}

        {error && run?.status !== "failed" && (
          <div className="animate-soft-in py-4">
            <AssistantIdentity />
            <div className="mt-3 pl-0 sm:pl-9">
              <div className="flex gap-2 rounded-xl bg-destructive/[0.055] px-3.5 py-3 text-xs text-destructive" role="alert">
                <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                <span>{error}</span>
              </div>
            </div>
          </div>
        )}
        <div ref={conversationEnd} />
      </div>

      <div className="sticky bottom-0 z-20 -mx-2 bg-gradient-to-t from-background via-background/98 to-transparent px-2 pb-3 pt-8 sm:pb-5">
        {run?.status === "completed" && (
          <div className="mb-2 flex items-center justify-center gap-2 text-[10px] text-muted-foreground">
            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
            Research complete · ask another question below
          </div>
        )}
        <ChatComposer
          value={draft}
          onChange={setDraft}
          file={file}
          onFileChange={setFile}
          onSubmit={submit}
          disabled={isWorking}
          busy={isWorking}
          compact
          onValidationError={setError}
        />
        <p className="mt-2 text-center text-[9px] text-muted-foreground/75">
          AMRRA can make mistakes in interpretation. Deterministic calculations remain separately validated.
        </p>
      </div>
    </div>
  )
}
