"use client"

import { Badge } from "@/components/ui/badge"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import {
  Braces,
  Check,
  ChevronDown,
  Circle,
  Clock3,
  DatabaseZap,
  FileCheck2,
  FileSearch,
  FlaskConical,
  Gauge,
  GitBranch,
  LoaderCircle,
  Scale,
  ScanText,
  ShieldAlert,
  Sparkles,
} from "lucide-react"

const STAGE_META = {
  ingestion: {
    label: "Ingestion",
    eyebrow: "Source boundary",
    description: "Normalize and validate research material before reasoning begins.",
    icon: FileCheck2,
  },
  retrieval: {
    label: "Retrieval",
    eyebrow: "Evidence search",
    description: "Select a bounded evidence set and semantically rerank only supplied chunks.",
    icon: FileSearch,
  },
  extraction: {
    label: "Extraction",
    eyebrow: "Grounded interpretation",
    description: "Turn evidence into typed hypotheses and observations with citation checks.",
    icon: ScanText,
  },
  planning: {
    label: "Planning",
    eyebrow: "Tool contract",
    description: "Choose a deterministic statistical path only when evidence satisfies its preconditions.",
    icon: GitBranch,
  },
  experimentation: {
    label: "Experimentation",
    eyebrow: "Deterministic compute",
    description: "Execute statistical tools outside the LLM and persist immutable results.",
    icon: FlaskConical,
  },
  judging: {
    label: "Judging",
    eyebrow: "Research synthesis",
    description: "Interpret immutable results, practical meaning, limitations and traceable citations.",
    icon: Scale,
  },
}

const STATUS_META = {
  pending: { label: "Waiting", className: "border-border bg-muted/45 text-muted-foreground" },
  active: { label: "Working", className: "border-primary/20 bg-primary/10 text-primary" },
  completed: { label: "Complete", className: "border-emerald-500/20 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300" },
  failed: { label: "Failed", className: "border-destructive/25 bg-destructive/10 text-destructive" },
}

function formatDuration(ms) {
  if (ms === null || ms === undefined) return null
  if (ms < 1000) return `${ms} ms`
  return `${(ms / 1000).toFixed(ms >= 10000 ? 0 : 1)} s`
}

function formatMetric(value) {
  if (value === null || value === undefined) return "—"
  const number = Number(value)
  if (!Number.isFinite(number)) return String(value)
  if (number !== 0 && Math.abs(number) < 0.001) return number.toExponential(2)
  if (Math.abs(number) >= 1000) return number.toLocaleString(undefined, { maximumFractionDigits: 2 })
  return number.toFixed(4).replace(/0+$/, "").replace(/\.$/, "")
}

function StatusMark({ status }) {
  if (status === "completed") {
    return <span className="grid h-7 w-7 place-items-center rounded-full bg-emerald-500 text-white shadow-sm"><Check className="h-4 w-4" strokeWidth={2.5} /></span>
  }
  if (status === "active") {
    return <span className="animate-status-pulse grid h-7 w-7 place-items-center rounded-full bg-primary/12 text-primary"><LoaderCircle className="h-4 w-4 animate-spin" /></span>
  }
  if (status === "failed") {
    return <span className="grid h-7 w-7 place-items-center rounded-full bg-destructive/12 text-destructive"><ShieldAlert className="h-4 w-4" /></span>
  }
  return <span className="grid h-7 w-7 place-items-center rounded-full border bg-background/70 text-muted-foreground"><Circle className="h-2.5 w-2.5" /></span>
}

function TraceMeta({ trace }) {
  if (!trace) return null
  const duration = formatDuration(trace.latency_ms)
  return (
    <div className="mt-4 flex flex-wrap gap-2 border-t pt-3 text-[11px] text-muted-foreground">
      {duration && <span className="inline-flex items-center gap-1.5 rounded-md bg-muted/55 px-2 py-1"><Clock3 className="h-3 w-3" />{duration}</span>}
      {trace.model && <span className="inline-flex items-center gap-1.5 rounded-md bg-muted/55 px-2 py-1"><Sparkles className="h-3 w-3" />{trace.model}</span>}
      {trace.prompt_version && <span className="inline-flex items-center gap-1.5 rounded-md bg-muted/55 px-2 py-1"><Braces className="h-3 w-3" />{trace.prompt_version}</span>}
      {trace.output_hash && <span className="rounded-md bg-muted/55 px-2 py-1 font-mono">out:{trace.output_hash.slice(0, 10)}</span>}
    </div>
  )
}

function IngestionWork({ run, trace }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      <MetricCard label="Downstream evidence" value={`${run?.evidence?.length || 0} chunks`} icon={DatabaseZap} />
      <MetricCard label="Boundary status" value={trace?.status === "completed" ? "Materialized" : "Awaiting source"} icon={FileCheck2} />
      <p className="sm:col-span-2 text-xs leading-5 text-muted-foreground">
        Source material is normalized before retrieval. The worker receives text content rather than relying on an uploaded local file path.
      </p>
    </div>
  )
}

function RetrievalWork({ run, trace }) {
  const evidence = run?.evidence || []
  if (!evidence.length) return <EmptyStage text="Relevant evidence chunks will appear here after retrieval completes." />

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <Badge variant="secondary">{evidence.length} evidence chunks</Badge>
        {trace?.metadata?.reranked !== undefined && <Badge variant="outline">{trace.metadata.reranked} model-reranked</Badge>}
      </div>
      <div className="space-y-2">
        {evidence.slice(0, 4).map((chunk, index) => (
          <div key={chunk.chunk_id} className="rounded-xl border bg-background/55 p-3 transition-colors hover:bg-background/90">
            <div className="flex items-center justify-between gap-3">
              <div className="min-w-0">
                <p className="truncate text-xs font-semibold">{chunk.source_title || `Evidence ${index + 1}`}</p>
                <p className="mt-0.5 truncate font-mono text-[10px] text-muted-foreground">{chunk.chunk_id}</p>
              </div>
              <span className="shrink-0 rounded-md bg-primary/8 px-2 py-1 font-mono text-[10px] font-semibold text-primary">
                score {formatMetric(chunk.metadata?.agent_relevance ?? chunk.score)}
              </span>
            </div>
            <p className="mt-2 line-clamp-3 text-xs leading-5 text-muted-foreground">{chunk.text}</p>
          </div>
        ))}
      </div>
      {evidence.length > 4 && <p className="text-[11px] text-muted-foreground">+ {evidence.length - 4} more persisted chunks available to downstream stages.</p>}
    </div>
  )
}

function ExtractionWork({ run, trace }) {
  const extraction = run?.extraction
  if (!extraction) return <EmptyStage text="Grounded hypotheses will appear after the Extractor validates model output against retrieved chunk IDs." />
  const hypotheses = extraction.hypotheses || []

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <Badge variant="secondary">{hypotheses.length} grounded {hypotheses.length === 1 ? "hypothesis" : "hypotheses"}</Badge>
        {trace?.metadata?.recovery_attempted && <Badge variant="outline">focused recovery used</Badge>}
        {trace?.metadata?.evidence_only_fallback && <Badge variant="outline">evidence-only path</Badge>}
      </div>
      {hypotheses.length ? hypotheses.map((hypothesis, index) => (
        <div key={hypothesis.hypothesis_id} className="rounded-xl border bg-background/55 p-3.5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-primary">Hypothesis {index + 1}</p>
              <p className="mt-1 text-sm font-medium leading-6">{hypothesis.statement}</p>
            </div>
            <span className="shrink-0 font-mono text-xs font-semibold text-muted-foreground">{Math.round((hypothesis.confidence || 0) * 100)}%</span>
          </div>
          <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-muted">
            <div className="h-full rounded-full bg-primary transition-[width] duration-700" style={{ width: `${Math.max(3, (hypothesis.confidence || 0) * 100)}%` }} />
          </div>
          <div className="mt-3 flex flex-wrap gap-1.5">
            {(hypothesis.evidence_chunk_ids || []).map((id) => <span key={id} className="rounded-md bg-muted/70 px-2 py-1 font-mono text-[10px] text-muted-foreground">{id}</span>)}
          </div>
        </div>
      )) : <EmptyStage text="No inferential hypothesis survived evidence grounding. AMRRA can still continue to an evidence-only judgement without fabricating data." />}
      {extraction.notes && <p className="rounded-xl bg-muted/45 p-3 text-xs leading-5 text-muted-foreground">{extraction.notes}</p>}
    </div>
  )
}

function PlanningWork({ run }) {
  const plans = run?.plans || []
  if (!plans.length) return <EmptyStage text="No statistical plan has been justified yet. Unsupported evidence remains descriptive instead of being forced into a test." />

  return (
    <div className="space-y-2">
      {plans.map((plan, index) => (
        <div key={`${plan.hypothesis_id}-${index}`} className="rounded-xl border bg-background/55 p-3.5">
          <div className="flex flex-wrap items-center gap-2">
            <Badge>{plan.test.replaceAll("_", " ")}</Badge>
            <span className="text-[10px] font-medium uppercase tracking-[0.15em] text-muted-foreground">deterministic selection</span>
          </div>
          <p className="mt-2 text-xs leading-5 text-muted-foreground">{plan.rationale}</p>
          {Object.keys(plan.input_data || {}).length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {Object.keys(plan.input_data).map((key) => <span key={key} className="rounded-md border bg-card px-2 py-1 font-mono text-[10px]">{key}</span>)}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

function ExperimentWork({ run }) {
  const experiments = run?.experiments || []
  if (!experiments.length) return <EmptyStage text="Deterministic statistical outputs will appear here when a plan satisfies a supported tool contract." />

  return (
    <div className="space-y-3">
      {experiments.map((result, index) => (
        <div key={`${result.hypothesis_id}-${index}`} className="rounded-xl border bg-background/55 p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex flex-wrap items-center gap-2">
              <Badge>{result.test_used}</Badge>
              <Badge variant="outline">{result.status.replaceAll("_", " ")}</Badge>
            </div>
            {result.status === "completed" && <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-[0.15em] text-emerald-600 dark:text-emerald-400"><Check className="h-3 w-3" /> computed</span>}
          </div>
          <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
            <MetricTile label="Statistic" value={formatMetric(result.statistic)} />
            <MetricTile label="p-value" value={formatMetric(result.p_value)} />
            <MetricTile label="Effect" value={formatMetric(result.effect_size)} />
            <MetricTile label="Estimate" value={Array.isArray(result.estimate) ? result.estimate.map(formatMetric).join(", ") : formatMetric(result.estimate)} />
          </div>
          <p className="mt-3 text-xs font-medium leading-5">{result.conclusion}</p>
          {result.method_notes && <p className="mt-1 text-[11px] leading-5 text-muted-foreground">{result.method_notes}</p>}
          {result.quality_flags?.length > 0 && <div className="mt-3 flex flex-wrap gap-1.5">{result.quality_flags.map((flag) => <Badge key={flag} variant="outline">{flag.replaceAll("_", " ")}</Badge>)}</div>}
        </div>
      ))}
    </div>
  )
}

function JudgingWork({ run }) {
  const report = run?.report
  if (!report) return <EmptyStage text="The Judge will synthesize immutable experiment results and evidence after the preceding stages complete." />

  return (
    <div className="space-y-4">
      <div>
        <p className="text-base font-semibold tracking-[-0.015em]">{report.title}</p>
        <p className="mt-2 text-sm leading-6 text-muted-foreground">{report.summary}</p>
      </div>
      <div className="rounded-xl border border-primary/15 bg-primary/7 p-3.5">
        <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-primary">Conclusion</p>
        <p className="mt-1.5 text-sm font-medium leading-6">{report.conclusion}</p>
      </div>
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <Gauge className="h-3.5 w-3.5" />
        Judge confidence <span className="font-mono font-semibold text-foreground">{Math.round((report.confidence || 0) * 100)}%</span>
      </div>
      {report.limitations?.length > 0 && (
        <div>
          <p className="text-xs font-semibold">Limitations</p>
          <ul className="mt-2 space-y-1.5 text-xs leading-5 text-muted-foreground">
            {report.limitations.map((item) => <li key={item} className="flex gap-2"><span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-muted-foreground" />{item}</li>)}
          </ul>
        </div>
      )}
      {report.citations?.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-semibold">Traceable citations</p>
          {report.citations.map((citation, index) => (
            <div key={`${citation.chunk_id}-${index}`} className="rounded-xl bg-muted/45 p-3 text-xs">
              <span className="font-mono text-[10px] font-semibold text-primary">{citation.chunk_id}</span>
              <p className="mt-1 leading-5 text-muted-foreground">{citation.claim}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function StageWork({ stage, run, trace }) {
  if (stage === "ingestion") return <IngestionWork run={run} trace={trace} />
  if (stage === "retrieval") return <RetrievalWork run={run} trace={trace} />
  if (stage === "extraction") return <ExtractionWork run={run} trace={trace} />
  if (stage === "planning") return <PlanningWork run={run} />
  if (stage === "experimentation") return <ExperimentWork run={run} />
  return <JudgingWork run={run} />
}

function MetricCard({ label, value, icon: Icon }) {
  return (
    <div className="rounded-xl border bg-background/55 p-3">
      <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.15em] text-muted-foreground"><Icon className="h-3.5 w-3.5" />{label}</div>
      <p className="mt-1.5 text-sm font-semibold">{value}</p>
    </div>
  )
}

function MetricTile({ label, value }) {
  return (
    <div className="rounded-lg bg-muted/45 p-2.5">
      <p className="text-[9px] font-bold uppercase tracking-[0.16em] text-muted-foreground">{label}</p>
      <p className="mt-1 truncate font-mono text-xs font-semibold" title={String(value)}>{value}</p>
    </div>
  )
}

function EmptyStage({ text }) {
  return (
    <div className="flex gap-3 rounded-xl border border-dashed bg-muted/20 p-3.5 text-xs leading-5 text-muted-foreground">
      <Circle className="mt-1 h-3 w-3 shrink-0" />
      <p>{text}</p>
    </div>
  )
}

export function AgentStageCard({ item, run, open, onOpenChange, index }) {
  if (!item?.stage || !STAGE_META[item.stage]) return null

  const meta = STAGE_META[item.stage]
  const statusMeta = STATUS_META[item.status] || STATUS_META.pending
  const Icon = meta.icon
  const trace = item.trace
  const animationIndex = Number.isFinite(index) ? index : 0

  return (
    <Collapsible open={open} onOpenChange={onOpenChange}>
      <div
        className={`group relative overflow-hidden rounded-2xl border bg-card/80 transition-all duration-300 ${
          item.status === "active"
            ? "border-primary/30 shadow-lg shadow-primary/8"
            : item.status === "failed"
              ? "border-destructive/30"
              : "hover:border-primary/18 hover:shadow-sm"
        }`}
        style={{ animationDelay: `${animationIndex * 45}ms` }}
      >
        {item.status === "active" && <div className="absolute inset-x-0 top-0 h-0.5 bg-gradient-to-r from-transparent via-primary to-transparent" />}
        <CollapsibleTrigger asChild>
          <button className="flex w-full items-center gap-3 p-4 text-left sm:p-4.5" aria-label={`${open ? "Hide" : "Show"} ${meta.label} work`}>
            <StatusMark status={item.status} />
            <div className="grid h-9 w-9 shrink-0 place-items-center rounded-xl border bg-background/70 text-muted-foreground transition-colors group-hover:text-primary">
              <Icon className="h-4 w-4" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                <span className="text-sm font-semibold tracking-[-0.01em]">{meta.label}</span>
                <span className="hidden text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground/70 sm:inline">{meta.eyebrow}</span>
              </div>
              <p className="mt-0.5 hidden truncate text-[11px] text-muted-foreground sm:block">{meta.description}</p>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <Badge variant="outline" className={`hidden h-6 rounded-full px-2 text-[10px] font-semibold sm:inline-flex ${statusMeta.className}`}>{statusMeta.label}</Badge>
              {trace?.latency_ms !== null && trace?.latency_ms !== undefined && <span className="hidden text-[10px] font-medium text-muted-foreground lg:inline">{formatDuration(trace.latency_ms)}</span>}
              <ChevronDown className={`h-4 w-4 text-muted-foreground transition-transform duration-200 ${open ? "rotate-180" : ""}`} />
            </div>
          </button>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <div className="border-t bg-muted/10 px-4 py-4 sm:px-5">
            <StageWork stage={item.stage} run={run} trace={trace} />
            <TraceMeta trace={trace} />
          </div>
        </CollapsibleContent>
      </div>
    </Collapsible>
  )
}
